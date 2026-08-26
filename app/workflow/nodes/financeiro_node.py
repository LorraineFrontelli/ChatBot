import logging

from langchain_core.runnables import RunnableConfig

from app.agentes import financial_app

logger = logging.getLogger(__name__)


def financeiro_node(state: dict, config: RunnableConfig) -> dict:
    """Repassa `config` pro invoke: é dali que a tool buscar_historico
    (registrada no financial_app) lê o thread_id da conversa."""
    entrada = state["resposta_roteador"]
    resposta = financial_app.invoke(
        {"messages": [{"role": "human", "content": entrada}]}, config=config
    )["messages"][-1].content
    logger.debug("Financeiro response: %s", resposta)
    return {"resposta_bruta": resposta, "agentes_chamados": ["financeiro"]}
