import operator
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, MessagesState, END
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent

from src.agentes.llms import llm_especialista, llm_rapido
from src.agentes.router.router_prompts import ROUTER_PROMPT
from src.agentes.financeiro.financeiro_prompts import FINANCIAL_PROMPT
from src.agentes.financeiro.tools import TOOLS
from src.agentes.agenda.agenda_prompts import AGENDA_PROMPT
from src.agentes.orquestrador.orquestrador_prompts import ORCHESTRATOR_PROMPT
from src.agentes.faq.faq_prompts import FAQ_PROMPT
from src.agentes.faq.tools.pdf_rag import faq_retriver


# ==============================================================================
# AGENTES
# ==============================================================================
router_app = create_agent(model=llm_rapido, system_prompt=ROUTER_PROMPT)
financeiro_app = create_agent(model=llm_especialista, tools=TOOLS, system_prompt=FINANCIAL_PROMPT)
agenda_app = create_agent(model=llm_especialista, system_prompt=AGENDA_PROMPT)
orquestrador_app = create_agent(model=llm_rapido, system_prompt=ORCHESTRATOR_PROMPT)
faq_app = create_agent(model=llm_rapido, tools=[faq_retriver], system_prompt=FAQ_PROMPT)


# ============================================================================== I
# ESTADO
# ==============================================================================
class Estado(TypedDict, total=False):
    input: str
    session_id: str
    saida_especialista: str
    resposta_final: str
    agentes_chamados:   Annotated[list[str], operator.add]  # acumula entre nós
    rota: str 


# ==============================================================================
# NÓS
# ==============================================================================
def no_roteador(estado: Estado) -> dict:
    saida = router_app.invoke(
        {"messages": [{"role": "human", "content": estado["input"]}]},
        config={"configurable": {"thread_id": estado["session_id"]}},
    )
    texto = saida["messages"][-1].text

    # Resposta direta (saudação, fora de escopo): já escreve no campo final
    if not texto.strip().startswith("ROUTE="):
        return {
            "agentes_chamados": ["roteador"],
            "resposta_final":   texto,
        }

    # Encaminhamento: sobrescreve input com o protocolo para o especialista
    return {
        "input":            texto,
        "agentes_chamados": ["roteador"],
    }


def no_orquestrador(estado: Estado) -> dict:
    saida = orquestrador_app.invoke(
        {"messages": [{"role": "human", "content": estado["saida_especialista"]}]},
        config={"configurable": {"thread_id": estado["session_id"]}},
    )
    return {
        "resposta_final":   saida["messages"][-1].text,
        "agentes_chamados": ["orquestrador"],
    }


# ==============================================================================
# FUNÇÃO DE DECISÃO
# ==============================================================================
def no_guardral_entrada(estado: Estado) -> dict:
    return {"agentes_chamados": ["guardrail_entrada"]}


def no_guardral_saida(estado: Estado) -> dict:
    return {"agentes_chamados": ["guardrail_saida"]}


def no_financeiro(estado: Estado) -> dict:
    saida = financeiro_app.invoke(
        {"messages": [{"role": "human", "content": estado["input"]}]},
        config={"configurable": {"thread_id": estado["session_id"]}},
    )
    return {
        "saida_especialista": saida["messages"][-1].text,
        "agentes_chamados": ["financeiro"],
    }


def no_agenda(estado: Estado) -> dict:
    saida = agenda_app.invoke(
        {"messages": [{"role": "human", "content": estado["input"]}]},
        config={"configurable": {"thread_id": estado["session_id"]}},
    )
    return {
        "saida_especialista": saida["messages"][-1].text,
        "agentes_chamados": ["agenda"],
    }


def no_faq(estado: Estado) -> dict:
    saida = faq_app.invoke(
        {"messages": [{"role": "human", "content": estado["input"]}]},
        config={"configurable": {"thread_id": estado["session_id"]}},
    )
    return {
        "resposta_final": saida["messages"][-1].text,
        "agentes_chamados": ["faq"],
    }


def decidir_especialista(estado: Estado) -> str:
    """Lê o protocolo do roteador e devolve o nome do próximo nó."""
    texto = estado["input"].strip()

    if not texto.startswith("ROUTE="):
        return "fim"   # resposta direta já foi escrita no nó do roteador

    rota = texto.split("\n", 1)[0].split("=", 1)[1].strip()
    return rota if rota in ("financeiro", "agenda", "faq") else "fim"


# ==============================================================================
# CONSTRUÇÃO DO GRAFO
# ==============================================================================
grafo = StateGraph(Estado)

grafo.add_node("guardrail_entrada", no_guardral_entrada)
grafo.add_node("roteador",     no_roteador)
grafo.add_node("financeiro",   no_financeiro)
grafo.add_node("agenda",       no_agenda)
grafo.add_node("faq",          no_faq)
grafo.add_node("orquestrador", no_orquestrador)
grafo.add_node("guardrail_saida", no_guardral_saida)


grafo.set_entry_point("roteador")

grafo.add_conditional_edges(
    "roteador",
    decidir_especialista,
    {
        "financeiro": "financeiro",
        "agenda":     "agenda",
        "faq":        "faq",
        "fim":        END,       # resposta direta: sem especialista nem orquestrador
    },
)

grafo.add_edge("financeiro",   "orquestrador")
grafo.add_edge("agenda",       "orquestrador")
grafo.add_edge("orquestrador", END)
grafo.add_edge("faq",          END)   # FAQ bypassa o orquestrador

# Memória centralizada no grafo — persiste o Estado inteiro entre turns
memory = MemorySaver()
fluxo_agentes = grafo.compile(checkpointer=memory)


# ==============================================================================
# FLUXO PRINCIPAL
# ==============================================================================
def executar_fluxo_assessor(pergunta_usuario: str, session_id: str) -> str:
    estado_inicial = {
        "input": pergunta_usuario,
        "session_id": session_id,
        "agentes_chamados": [],
    }

    estado_final = fluxo_agentes.invoke(
        estado_inicial,
        config={"configurable": {"thread_id": session_id}},
    )

    print(f"[debug] agentes chamados: {estado_final['agentes_chamados']}")
    return estado_final["resposta_final"]


# ==============================================================================
# LOOP DE CONVERSA
# ==============================================================================
if __name__ == "__main__":
    while True:
        try:
            user_input = input("> ")
            if user_input.lower() in ("sair", "end", "fim", "tchau", "bye"):
                print("Encerrando a conversa.")
                break

            resposta = executar_fluxo_assessor(
                pergunta_usuario=user_input,
            session_id="id_usuario_mas_agora_não_importa",
            )
            print(resposta)

        except Exception as e:
            print("Erro ao consumir a API:", e)
            continue
