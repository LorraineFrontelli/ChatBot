import logging

from langchain_core.runnables import RunnableConfig

from app.agentes import router_app
from app.workflow.edges.routing_edges import ROTAS_VALIDAS, match_agent

logger = logging.getLogger(__name__)


def router_node(state: dict, config: RunnableConfig) -> dict:
    """Invoca o roteador. Se ele apontar ROUTE=<agente>, segue pro
    especialista; se não, é resposta direta (saudação/fora de escopo, ou
    memória de conversas anteriores via buscar_historico).

    Recebe `config` do LangGraph (por declarar o parâmetro aqui) e repassa
    pro invoke: é dali que a tool buscar_historico lê o thread_id da conversa.
    Sem repassar, a tool fica registrada no agente mas nunca sabe de quem é
    o histórico — e responde "não foi possível identificar a sessão".
    """
    pergunta = state["pergunta_anonimizada"]

    resposta = router_app.invoke(
        {"messages": [{"role": "human", "content": pergunta}]}, config=config
    )["messages"][-1].content
    logger.debug("Router response: %s", resposta)

    agente = match_agent(resposta)

    if agente in ROTAS_VALIDAS:
        return {"rota": agente, "resposta_roteador": resposta, "agentes_chamados": ["router"]}

    logger.info("Nenhum agente casado. Roteador respondendo diretamente.")
    return {"rota": "direto", "resposta_bruta": resposta, "agentes_chamados": ["router"]}
