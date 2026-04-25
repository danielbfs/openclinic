"""AI Engine — orchestrates LLM conversations with function calling."""
import json
import logging

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.ai.config_loader import load_ai_config, load_chatbot_config, load_clinic_config
from app.modules.ai.prompts import build_system_prompt
from app.modules.ai.session import load_session, save_session
from app.modules.ai.tools import TOOL_DEFINITIONS, execute_tool
from app.modules.crm.models import Patient

logger = logging.getLogger(__name__)


def _get_client(ai_config: dict) -> AsyncOpenAI:
    """Get the appropriate LLM client based on DB config."""
    if ai_config.get("use_local_llm") and ai_config.get("local_llm_url"):
        return AsyncOpenAI(
            base_url=ai_config["local_llm_url"],
            api_key="not-needed",
        )
    # Fallback: check env for local LLM
    if settings.LOCAL_LLM_BASE_URL:
        return AsyncOpenAI(
            base_url=settings.LOCAL_LLM_BASE_URL,
            api_key="not-needed",
        )
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def _get_model(ai_config: dict) -> str:
    if ai_config.get("use_local_llm") and ai_config.get("local_llm_model"):
        return ai_config["local_llm_model"]
    if settings.LOCAL_LLM_BASE_URL and settings.LOCAL_LLM_MODEL:
        return settings.LOCAL_LLM_MODEL
    return ai_config.get("model") or settings.OPENAI_MODEL


async def process_message(
    db: AsyncSession,
    patient: Patient,
    user_text: str,
) -> str:
    """Process an incoming patient message and return the AI response."""
    if not settings.OPENAI_API_KEY and not settings.LOCAL_LLM_BASE_URL:
        # Also check DB config
        ai_config = await load_ai_config(db)
        if not ai_config.get("use_local_llm") or not ai_config.get("local_llm_url"):
            logger.warning("No LLM configured (OPENAI_API_KEY or LOCAL_LLM_BASE_URL)")
            return (
                "O assistente virtual está temporariamente indisponível. "
                "Por favor, entre em contato pelo telefone da clínica."
            )
    else:
        ai_config = await load_ai_config(db)

    chatbot_config = await load_chatbot_config(db)
    clinic_config = await load_clinic_config(db)

    client = _get_client(ai_config)
    model = _get_model(ai_config)
    max_tool_calls = chatbot_config.get("max_tool_calls", 3)
    temperature = chatbot_config.get("temperature", 0.3)

    # Load conversation history
    history = await load_session(patient.id)

    # Build messages
    system_prompt = build_system_prompt(
        custom_prompt=chatbot_config.get("system_prompt", ""),
        clinic_name=clinic_config.get("name", ""),
        clinic_timezone=clinic_config.get("timezone", settings.CLINIC_TIMEZONE),
    )
    patient_context = (
        f"Paciente atual: {patient.full_name or 'nome não informado'} "
        f"(ID: {patient.id})"
    )

    messages = [
        {"role": "system", "content": f"{system_prompt}\n\n{patient_context}"},
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    # LLM loop with tool calls
    tool_calls_count = 0
    response_text = ""

    try:
        while tool_calls_count <= max_tool_calls:
            completion = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=temperature,
                max_tokens=1000,
            )

            choice = completion.choices[0]
            assistant_message = choice.message

            if assistant_message.tool_calls:
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_message.tool_calls
                    ],
                })

                # Execute each tool call
                for tc in assistant_message.tool_calls:
                    tool_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    logger.info(
                        "Tool call: %s(%s) for patient %s",
                        tool_name, args, patient.id,
                    )

                    result = await execute_tool(tool_name, args, db, patient.id)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

                tool_calls_count += 1
            else:
                # Final text response
                response_text = assistant_message.content or ""
                break
        else:
            response_text = (
                "Desculpe, estou tendo dificuldades para processar seu pedido. "
                "Vou encaminhar para a secretária."
            )

    except Exception:
        logger.exception("LLM API error for patient %s", patient.id)
        return (
            "Desculpe, ocorreu um erro ao processar sua mensagem. "
            "Por favor, tente novamente."
        )

    # Save updated history (keep only user/assistant messages for storage)
    session_messages = _extract_storable_messages(history, user_text, response_text)
    await save_session(patient.id, session_messages)

    return response_text


def _extract_storable_messages(
    history: list[dict],
    user_text: str,
    assistant_text: str,
) -> list[dict]:
    """Keep only user/assistant turns for Redis storage (no system/tool messages)."""
    storable = [
        msg for msg in history
        if msg.get("role") in ("user", "assistant") and "tool_calls" not in msg
    ]
    storable.append({"role": "user", "content": user_text})
    if assistant_text:
        storable.append({"role": "assistant", "content": assistant_text})
    return storable
