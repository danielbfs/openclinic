"""System prompts for the AI engine."""
from datetime import datetime, timezone

from app.config import settings

DEFAULT_PROMPT = """Suas responsabilidades:
1. Atender pacientes com cordialidade e profissionalismo
2. Verificar disponibilidade e agendar consultas
3. Confirmar, cancelar ou remarcar consultas existentes
4. Coletar informações básicas (nome, queixa principal)
5. Responder dúvidas gerais sobre a clínica

Regras IMPORTANTES:
- NUNCA invente horários. Use SEMPRE a ferramenta check_availability para consultar disponibilidade real
- Se o paciente quiser agendar, pergunte a especialidade ou médico desejado e a data de preferência
- Ao oferecer horários, apresente no máximo 5 opções de forma clara
- Antes de confirmar um agendamento, SEMPRE pergunte ao paciente se o horário está ok
- Se o paciente fizer perguntas médicas, oriente-o a consultar o médico
- Se não conseguir resolver algo, use escalate_to_human para transferir à secretária
- Fale em português do Brasil, com tom profissional mas acolhedor
- Seja conciso — mensagens curtas e diretas são melhores em chat
- Formate datas como "segunda-feira, 28 de abril às 14:00"
"""


def build_system_prompt(
    custom_prompt: str = "",
    clinic_name: str = "",
    clinic_timezone: str = "",
    specialties: list[dict] | None = None,
    doctors: list[dict] | None = None,
) -> str:
    """Build the system prompt with current clinic context.

    `specialties` and `doctors` are lists of dicts the LLM uses to pick UUIDs
    when calling tools (check_availability, book_appointment).
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    tz = clinic_timezone or settings.CLINIC_TIMEZONE
    name = clinic_name or "a clínica"

    header = f"Você é o assistente virtual de {name}."
    context = f"""
Fuso horário da clínica: {tz}
Data/hora atual: {now}
"""

    catalog_parts = []
    if specialties:
        lines = "\n".join(f"- {s['name']} (id: {s['id']})" for s in specialties)
        catalog_parts.append(f"Especialidades disponíveis:\n{lines}")
    if doctors:
        lines = "\n".join(
            f"- {d['full_name']} (id: {d['id']}"
            + (f", especialidade: {d['specialty_name']}" if d.get("specialty_name") else "")
            + ")"
            for d in doctors
        )
        catalog_parts.append(f"Médicos ativos:\n{lines}")
    catalog = ("\n\n" + "\n\n".join(catalog_parts)) if catalog_parts else ""

    # Use custom prompt from admin if provided, otherwise use default
    instructions = custom_prompt.strip() if custom_prompt.strip() else DEFAULT_PROMPT

    return f"{header}\n{context}{catalog}\n\n{instructions}"
