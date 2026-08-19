import logging

from app.agentes import financial_app

logger = logging.getLogger(__name__)


def financeiro_node(state: dict) -> dict:
    entrada = state["resposta_roteador"]
    resposta = financial_app.invoke(
        {"messages": [{"role": "human", "content": entrada}]}
    )["messages"][-1].content
    logger.debug("Financeiro response: %s", resposta)
    return {"resposta_bruta": resposta, "agentes_chamados": ["financeiro"]}
