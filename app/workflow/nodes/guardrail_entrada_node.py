import logging

from app.guardrail import guardrail_entrada

logger = logging.getLogger(__name__)


def guardrail_entrada_node(state: dict) -> dict:
    """A mensagem já chega anonimizada — executar_fluxo faz isso antes de
    invocar o grafo. Aqui só roda as checagens de segurança."""
    mensagem_anon = state["messages"][-1].content
    mapa_pii = state.get("mapa_pii", {})

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
