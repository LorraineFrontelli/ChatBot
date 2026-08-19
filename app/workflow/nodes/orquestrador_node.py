import logging

from app.agentes import orquestrator_app

logger = logging.getLogger(__name__)


def orquestrador_node(state: dict) -> dict:
    entrada = state["resposta_bruta"]
    resposta = orquestrator_app.invoke(
        {"messages": [{"role": "human", "content": entrada}]}
    )["messages"][-1].content
    logger.debug("Orquestrador response: %s", resposta)
    return {"resposta_bruta": resposta, "agentes_chamados": ["orquestrador"]}
