"""
Tool de memória de longo prazo — consulta conversas ANTERIORES do usuário.

Fica em app/memory/ (e não em app/agentes/<algum>/tools/) porque não tem um
dono único: é usada pelo router, financeiro e agenda, cada um pra uma coisa
diferente (ver ROUTER_PROMPT / FINANCIAL_PROMPT / AGENDA_PROMPT).
"""

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig

# ==============================================================================
# IMPORT DE session_summary FICA DENTRO DA FUNÇÃO (não aqui no topo)
# ------------------------------------------------------------------------------
# session_summary.py importa app.agentes.llms (pro LLM que gera o resumo), o
# que força o Python a carregar o pacote app.agentes inteiro — e é lá que
# router_app/financial_app/agenda_app importam esta tool de volta. Se
# `buscar_resumos` fosse importado aqui no topo do arquivo, o carregamento de
# qualquer um dos dois lados no meio do outro vira um import circular
# (ImportError: "partially initialized module"). Adiando o import pra dentro
# da função quebra o ciclo: nesse ponto todos os módulos já terminaram de
# carregar.
# ==============================================================================
# POR QUE user_id, NÃO session_id
# ------------------------------------------------------------------------------
# session_id é um UUID que o front troca a cada "nova sessão" (ver
# frontend/app.js) — bom pra delimitar um BLOCO de conversa, ruim pra achar
# histórico: some ao trocar de sessão/dispositivo. user_id vem do JWT (ver
# get_current_user_id, app/security.py) e é estável pra sempre pro mesmo
# usuário, então buscar_resumos() filtra por ele — alcança blocos resumidos
# de qualquer sessão/dispositivo, não só o mesmo navegador ainda aberto.
# ==============================================================================


@tool
def buscar_historico(busca: str, config: RunnableConfig) -> str:
    """Consulta conversas ANTERIORES do usuário (sessões já encerradas).

    Use SOMENTE quando a resposta depende de algo dito numa conversa passada
    — preferências, decisões ou planos que o usuário mencionou antes.
    NÃO use para dados que estão no banco (gastos, saldos, eventos): para isso
    já existem as tools de consulta específicas como query_transactions,
    total_balance, daily_balance.

    Args:
        busca: assunto a procurar nos resumos das conversas anteriores.
    """
    from app.memory.log.session_summary import buscar_resumos  # ver comentário no topo do arquivo

    user_id = (config or {}).get("configurable", {}).get("user_id")

    if user_id is None:
        return "Não foi possível identificar o usuário para buscar o histórico."

    resumos = buscar_resumos(user_id, busca=busca, limite=3)

    if not resumos:
        return "Nenhuma conversa anterior relevante encontrada."

    return "\n\n".join(
        f"[{r['encerrada_em']:%d/%m/%Y}] {r['resumo']}" for r in resumos
    )


TOOLS_MEMORIA = [buscar_historico]
