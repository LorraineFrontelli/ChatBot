import logging

from app.guardrail import guardrail_saida

logger = logging.getLogger(__name__)


def guardrail_saida_node(state: dict) -> dict:
    """Remove PII gerada, desanonimiza via mapa_pii e revisa compliance.
    Nunca bloqueia (guardrail_saida já é fail-safe: se a revisão de
    compliance falhar, entrega o texto já limpo de PII sem a revisão extra)."""
    resposta_bruta = state.get("resposta_bruta", "")
    mapa_pii = state.get("mapa_pii", {})

    saida = guardrail_saida(resposta_bruta, mapa_pii)

    return {
        "messages": [{"role": "assistant", "content": saida["conteudo"]}],
        "agentes_chamados": ["guardrail_saida"],
    }
