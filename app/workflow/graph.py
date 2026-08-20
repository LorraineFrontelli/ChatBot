from langgraph.graph import END, StateGraph

from app.guardrail import anonimizar_entrada
from app.memory.session.mongo_checkpointer import get_checkpointer
from app.workflow.edges.routing_edges import decidir_pos_guardrail_entrada, decidir_pos_router
from app.workflow.nodes.agenda_node import agenda_node
from app.workflow.nodes.faq_node import faq_node
from app.workflow.nodes.financeiro_node import financeiro_node
from app.workflow.nodes.guardrail_entrada_node import guardrail_entrada_node
from app.workflow.nodes.guardrail_saida_node import guardrail_saida_node
from app.workflow.nodes.orquestrador_node import orquestrador_node
from app.workflow.nodes.router_node import router_node
from app.workflow.state.state import Estado


def build_graph():
    grafo = StateGraph(Estado)
    grafo.add_node("guardrail_entrada", guardrail_entrada_node)
    grafo.add_node("router", router_node)
    grafo.add_node("financeiro", financeiro_node)
    grafo.add_node("agenda", agenda_node)
    grafo.add_node("faq", faq_node)
    grafo.add_node("orquestrador", orquestrador_node)
    grafo.add_node("guardrail_saida", guardrail_saida_node)

    grafo.set_entry_point("guardrail_entrada")
    grafo.add_conditional_edges("guardrail_entrada", decidir_pos_guardrail_entrada,
        {"router": "router", "fim": END})
    grafo.add_conditional_edges("router", decidir_pos_router,
        {"financeiro": "financeiro", "agenda": "agenda", "faq": "faq",
         "guardrail_saida": "guardrail_saida"})

    grafo.add_edge("financeiro", "orquestrador")
    grafo.add_edge("agenda", "orquestrador")
    grafo.add_edge("faq", "guardrail_saida")
    grafo.add_edge("orquestrador", "guardrail_saida")
    grafo.add_edge("guardrail_saida", END)

    return grafo.compile(checkpointer=get_checkpointer())


fluxo_agentes = build_graph()


def executar_fluxo(pergunta: str, session_id: str) -> dict:
    """É isto que a rota /chat chama."""
    mensagem_anon, mapa_pii = anonimizar_entrada(pergunta)

    resultado = fluxo_agentes.invoke(
        {"messages": [{"role": "human", "content": mensagem_anon}], "mapa_pii": mapa_pii},
        config={"configurable": {"thread_id": session_id}},
    )
    return {
        "resposta": resultado["messages"][-1].content,
        "agentes_chamados": resultado.get("agentes_chamados", []),
        "pergunta_anonimizada": mensagem_anon,
    }
