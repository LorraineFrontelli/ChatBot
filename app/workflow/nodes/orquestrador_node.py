import logging

from langchain_core.runnables import RunnableConfig

from app.agentes import orquestrator_app

logger = logging.getLogger(__name__)


def orquestrador_node(state: dict, config: RunnableConfig) -> dict:
    """Repassa `config` pelo mesmo motivo do roteador: sem ele, o modelo deste
    nó não herda o metadata do grafo e o registro de observabilidade perde o nó."""
    entrada = state["resposta_bruta"]
    resposta = orquestrator_app.invoke(
        {"messages": [{"role": "human", "content": entrada}]}, config=config
    )["messages"][-1].content
    logger.debug("Orquestrador response: %s", resposta)
    return {"resposta_bruta": resposta, "agentes_chamados": ["orquestrador"]}
