"""System prompts for the AI engine."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

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
- Ao oferecer horários, apresente no máximo 5 opções de forma clara usando o campo "display" retornado pela ferramenta
- Antes de confirmar um agendamento, SEMPRE pergunte ao paciente se o horário está ok
- Se o paciente fizer perguntas médicas, oriente-o a consultar o médico
- Se não conseguir resolver algo, use escalate_to_human para transferir à secretária
- Fale em português do Brasil, com tom profissional mas acolhedor
- Seja conciso — mensagens curtas e diretas são melhores em chat
- Formate datas como "segunda-feira, 28 de abril às 14:00"

Regras para LEADS (oportunidades):
- Se o paciente pedir orçamento, preço, ou quiser saber mais antes de agendar → use create_lead para registrá-lo no CRM
- Se o paciente demonstrar interesse mas sair sem marcar consulta → use create_lead
- Ao criar o lead, colete: nome, especialidade de interesse e o que o paciente busca
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
    tz = clinic_timezone or settings.CLINIC_TIMEZONE
    name = clinic_name or "a clínica"
    # Always show current time in clinic local timezone so LLM knows correct local hour
    clinic_tz = ZoneInfo(tz)
    now_local = datetime.now(timezone.utc).astimezone(clinic_tz)
    now = now_local.strftime("%Y-%m-%d %H:%M") + f" ({tz})"

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

    # Esta seção é SEMPRE incluída, independente do prompt personalizado do admin.
    # Garante que o LLM saiba exatamente quando chamar cada ferramenta.
    tool_rules = """
---
REGRAS DE USO DAS FERRAMENTAS (obrigatórias, não alterar):
- check_availability → use SEMPRE que o paciente quiser saber horários disponíveis. Nunca invente horários.
- book_appointment → use SOMENTE após o paciente confirmar o horário escolhido.
- create_lead → use OBRIGATORIAMENTE quando: (a) paciente perguntar preço ou orçamento; (b) paciente demonstrar interesse mas não quiser agendar agora; (c) paciente quiser mais informações antes de decidir. Colete: nome, especialidade de interesse e motivo.
- escalate_to_human → use quando não conseguir resolver. Ao escalar, o sistema criará o lead automaticamente.
- Ao exibir horários, use o campo "display" retornado pela ferramenta (ex: "28/04/2026 08:00").
"""

    return f"{header}\n{context}{catalog}\n\n{instructions}\n{tool_rules}"
