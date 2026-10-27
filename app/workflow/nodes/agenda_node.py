import logging

from langchain_core.runnables import RunnableConfig

from app.agentes import agenda_app
from app.workflow.nodes.juiz_node import coletar_evidencia

logger = logging.getLogger(__name__)


def agenda_node(state: dict, config: RunnableConfig) -> dict:
    """Repassa `config` pro invoke: é dali que a tool buscar_historico
    (registrada no agenda_app) lê o thread_id da conversa."""
    entrada = state["resposta_roteador"]
    resultado = agenda_app.invoke(
        {"messages": [{"role": "human", "content": entrada}]}, config=config
    )
    resposta = resultado["messages"][-1].content
    logger.debug("Agenda response: %s", resposta)
    return {
        "resposta_bruta": resposta,
        "evidencia": coletar_evidencia(resultado["messages"]),
        "agentes_chamados": ["agenda"],
    }
