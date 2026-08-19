import logging

from app.agentes import router_app
from app.workflow.edges.routing_edges import ROTAS_VALIDAS, match_agent

logger = logging.getLogger(__name__)


def router_node(state: dict) -> dict:
    """Invoca o roteador. Se ele apontar ROUTE=<agente>, segue pro
    especialista; se não, é resposta direta (saudação/fora de escopo)."""
    pergunta = state["pergunta_anonimizada"]

    resposta = router_app.invoke(
        {"messages": [{"role": "human", "content": pergunta}]}
    )["messages"][-1].content
    logger.debug("Router response: %s", resposta)

    agente = match_agent(resposta)

    if agente in ROTAS_VALIDAS:
        return {"rota": agente, "resposta_roteador": resposta, "agentes_chamados": ["router"]}

    logger.info("Nenhum agente casado. Roteador respondendo diretamente.")
    return {"rota": "direto", "resposta_bruta": resposta, "agentes_chamados": ["router"]}
