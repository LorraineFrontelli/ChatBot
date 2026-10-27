import logging

from app.agentes import faq_reader_app
from app.workflow.nodes.juiz_node import coletar_evidencia

logger = logging.getLogger(__name__)


def faq_node(state: dict) -> dict:
    """FAQ não passa pelo orquestrador — o prompt já responde em linguagem
    natural, não em JSON estruturado como financeiro/agenda."""
    entrada = state["resposta_roteador"]
    resultado = faq_reader_app.invoke(
        {"messages": [{"role": "human", "content": entrada}]}
    )
    resposta = resultado["messages"][-1].content
    logger.debug("FAQ response: %s", resposta)
    return {
        "resposta_bruta": resposta,
        "evidencia": coletar_evidencia(resultado["messages"]),
        "agentes_chamados": ["faq"],
    }
