import logging

from app.agentes import faq_reader_app

logger = logging.getLogger(__name__)


def faq_node(state: dict) -> dict:
    """FAQ não passa pelo orquestrador — o prompt já responde em linguagem
    natural, não em JSON estruturado como financeiro/agenda."""
    entrada = state["resposta_roteador"]
    resposta = faq_reader_app.invoke(
        {"messages": [{"role": "human", "content": entrada}]}
    )["messages"][-1].content
    logger.debug("FAQ response: %s", resposta)
    return {"resposta_bruta": resposta, "agentes_chamados": ["faq"]}
