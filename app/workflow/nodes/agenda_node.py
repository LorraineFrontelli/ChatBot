import logging

from app.agentes import agenda_app

logger = logging.getLogger(__name__)


def agenda_node(state: dict) -> dict:
    entrada = state["resposta_roteador"]
    resposta = agenda_app.invoke(
        {"messages": [{"role": "human", "content": entrada}]}
    )["messages"][-1].content
    logger.debug("Agenda response: %s", resposta)
    return {"resposta_bruta": resposta, "agentes_chamados": ["agenda"]}
