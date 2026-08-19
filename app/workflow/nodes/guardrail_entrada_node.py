import logging

from app.guardrail import anonimizar_entrada, guardrail_entrada

logger = logging.getLogger(__name__)


def guardrail_entrada_node(state: dict) -> dict:
    """Anonimiza a entrada e roda as checagens de segurança. Se a
    classificação via LLM falhar, bloqueia por padrão (fail-closed) em vez
    de deixar a mensagem passar sem checagem."""
    user_input = state["messages"][-1].content

    mensagem_anon, mapa_pii = anonimizar_entrada(user_input)

    try:
        check = guardrail_entrada(mensagem_anon)
    except Exception:
        logger.exception("Guardrail de entrada falhou; bloqueando por padrão.")
        check = {
            "bloqueado": True,
            "motivo": "erro_guardrail",
            "mensagem": "Sinto muito, não consegui processar sua mensagem agora. Tente novamente em instantes.",
        }

    if check["bloqueado"]:
        logger.info("Mensagem bloqueada pelo guardrail de entrada: %s", check["motivo"])
        return {
            "rota": "bloqueado",
            "mapa_pii": mapa_pii,
            "messages": [{"role": "assistant", "content": check["mensagem"]}],
            "agentes_chamados": ["guardrail_entrada"],
        }

    return {
        "rota": "",
        "mapa_pii": mapa_pii,
        "pergunta_anonimizada": mensagem_anon,
        "agentes_chamados": ["guardrail_entrada"],
    }
