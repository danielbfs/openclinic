"""Máquina de estados do pipeline de leads.

Padrão de pipeline B2C (HubSpot/Pipedrive/RD): cada lead atravessa etapas
discretas que reflitam o avanço comercial. As transições são livres dentro
do conjunto não-terminal — um lead pode pular ou voltar etapas conforme a
realidade do contato — mas estados terminais (convertido) bloqueiam o
movimento, e ``perdido`` só pode ser reaberto para retomar a abordagem.
"""
from __future__ import annotations

# Ordem canônica do pipeline (usada para Kanban)
PIPELINE_ORDER: list[str] = [
    "novo",
    "em_contato",
    "qualificado",
    "orcamento_enviado",
    "negociando",
    "convertido",
]

# Todos os status válidos (incluindo terminais e perdido)
LEAD_STATUSES: list[str] = PIPELINE_ORDER + ["perdido"]

# Status terminais — não podem mudar mais
TERMINAL_STATUSES: set[str] = {"convertido"}

# Status que requerem motivo
REQUIRES_LOST_REASON: set[str] = {"perdido"}

# Status que requerem criação de paciente
REQUIRES_PATIENT: set[str] = {"convertido"}

# Mapa de transições permitidas (origem → destinos)
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "novo": {"em_contato", "qualificado", "orcamento_enviado", "negociando", "convertido", "perdido"},
    "em_contato": {"qualificado", "orcamento_enviado", "negociando", "convertido", "perdido"},
    "qualificado": {"em_contato", "orcamento_enviado", "negociando", "convertido", "perdido"},
    "orcamento_enviado": {"em_contato", "qualificado", "negociando", "convertido", "perdido"},
    "negociando": {"em_contato", "qualificado", "orcamento_enviado", "convertido", "perdido"},
    "convertido": set(),
    "perdido": {"em_contato", "qualificado", "orcamento_enviado", "negociando"},
}

# Motivos padronizados de perda (drop-down)
LOST_REASONS: list[dict[str, str]] = [
    {"value": "sem_resposta", "label": "Sem resposta"},
    {"value": "preco", "label": "Preço"},
    {"value": "ja_atendido", "label": "Já atendido em outro lugar"},
    {"value": "fora_de_perfil", "label": "Fora do perfil"},
    {"value": "sem_disponibilidade", "label": "Sem disponibilidade"},
    {"value": "mudou_de_ideia", "label": "Mudou de ideia"},
    {"value": "duplicado", "label": "Lead duplicado"},
    {"value": "outro", "label": "Outro"},
]

STATUS_LABELS: dict[str, str] = {
    "novo": "Novo",
    "em_contato": "Em Contato",
    "qualificado": "Qualificado",
    "orcamento_enviado": "Orçamento Enviado",
    "negociando": "Negociando",
    "convertido": "Convertido",
    "perdido": "Perdido",
}


class InvalidTransitionError(ValueError):
    """Transição de status não permitida."""


def validate_transition(from_status: str, to_status: str) -> None:
    """Levanta InvalidTransitionError se a transição for inválida."""
    if to_status not in LEAD_STATUSES:
        raise InvalidTransitionError(f"Status inválido: {to_status}")
    if from_status == to_status:
        raise InvalidTransitionError(
            f"Lead já está em '{to_status}'."
        )
    allowed = ALLOWED_TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        raise InvalidTransitionError(
            f"Transição '{from_status}' → '{to_status}' não permitida. "
            f"Permitidos: {sorted(allowed) or 'nenhum (status terminal)'}"
        )
