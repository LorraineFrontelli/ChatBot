from .agentes import router_app, orquestrator_app, SPECIALISTS, CONSULTANTS
from .infraestrutura.md_console import print
from .infraestrutura.logger import setup_logger
from .core.guardrails import anonimizar_entrada, guardrail_entrada, guardrail_saida
from .infraestrutura.memory_mongodb import iniciar_sessao, salvar_mensagem, encerrar_sessao

from typing import Optional

import logging
import os
import re

setup_logger()
logger = logging.getLogger(__name__)


def invoke_agent(agent, user_input: str, session_id: str) -> str:
    response = agent.invoke(
        {"messages": [{"role": "human", "content": user_input}]},
        config={"configurable": {"thread_id": session_id}},
    )
    return response["messages"][-1].text


def invoke_specialist(specialist, router_response: str, session_id: str) -> str:
    specialist_response = invoke_agent(specialist, router_response, session_id)
    logger.debug("Specialist response: %s", specialist_response)

    logger.info("Agent invoked: orquestrator -> input = %s", specialist_response)
    response = invoke_agent(orquestrator_app, specialist_response, session_id)
    logger.debug("Orquestrator response: %s", response)
    return response


def invoke_consultant(consultant, router_response: str, session_id: str) -> str:
    response = invoke_agent(consultant, router_response, session_id)
    logger.debug("Consultant response: %s", response)
    return response


def match_agent(router_response: str) -> Optional[str]:
    match = re.search(r"(?<=ROUTE=)\w+", router_response)
    if not match:
        return None

    agent_name = match.group()
    logger.debug("Matched agent: %s from input: %s", agent_name, router_response)
    return agent_name


def make_question(user_input: str, session_id: str) -> str:
    try:
        salvar_mensagem(session_id, "usuario", user_input)
        mensagem_anon, mapa_pii = anonimizar_entrada(user_input)

        check = guardrail_entrada(mensagem_anon)
        if check["bloqueado"]:
            salvar_mensagem(session_id, "assistente", check["mensagem"])
            return check["mensagem"]
        
        logger.info("Agent invoked: router -> input = %s", mensagem_anon)
        router_response = invoke_agent(router_app, mensagem_anon, session_id)
        logger.debug("Router response: %s", router_response)

        if not (agent_name := match_agent(router_response)):
            logger.info("No agent matched. Router answering directly to user.")
            saida = guardrail_saida(router_response, mapa_pii)
            salvar_mensagem(session_id, "assistente", saida["conteudo"])
            return saida["conteudo"]

        if specialist := SPECIALISTS.get(agent_name):
            logger.info(
                "Specialist invoked: %s -> input = %s", agent_name, router_response
            )
            response = invoke_specialist(specialist, router_response, session_id)
            saida = guardrail_saida(response, mapa_pii)
            salvar_mensagem(session_id, "assistente", saida["conteudo"])
            return saida["conteudo"]

        if consultant := CONSULTANTS.get(agent_name):
            logger.info(
                "Consultant invoked: %s -> input = %s", agent_name, router_response
            )
            response = invoke_consultant(consultant, router_response, session_id)
            saida = guardrail_saida(response, mapa_pii)
            salvar_mensagem(session_id, "assistente", saida["conteudo"])
            return saida["conteudo"]

        logger.error("Router agent tried to access an unexisting agent: %s", agent_name)
        return f"Erro no roteador: agente {agent_name} não encontrado"

    except Exception:
        logger.exception("Exception raised while invoking agent")
        return f"Sinto muito, tivemos um erro interno. Tente novamente mais tarde."


logger.info("App started")
os.system("cls")
print("\n# Bem vindo! Converse hoje mesmo com o Assessor.IA!!\n")

SESSION_ID = "meu_id_de_sessao"
iniciar_sessao(SESSION_ID)

while True:
    user_input = input(">>> ")
    if user_input.lower() in ("sair", "exit", "tchau", "bye", "end", "fim"):
        print("Encerrando a conversa")
        encerrar_sessao(SESSION_ID)
        break

    response = make_question(user_input, SESSION_ID)
    print(f"\n{response}\n\n---\n\n")

logger.info("App closed")
