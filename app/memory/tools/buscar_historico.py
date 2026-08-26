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
# POR QUE SÓ thread_id, SEM user_id
# ------------------------------------------------------------------------------
# O front gera um UUID novo a cada "nova sessão" (ver frontend/app.js), e é
# esse UUID que vira o thread_id do checkpointer (executar_fluxo, em
# app/workflow/graph.py). Não existe hoje nenhum identificador mais estável
# de USUÁRIO no projeto — nem no schemas.py, nem nas rotas.
#
# Então isto não é um fallback temporário: é o único identificador que existe.
# Na prática, ele só encontra resumos de blocos fechados por INATIVIDADE
# dentro da MESMA sessão de navegador ainda aberta (ver session_summary.py) —
# um mesmo session_id pode acumular vários blocos resumidos sem que o usuário
# clique em "nova sessão". Não alcança conversas de outro dispositivo, nem
# depois de "nova sessão"/limpar o navegador: pra isso precisaria existir um
# user_id fixo, que o front ainda não manda.
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

    configuravel = (config or {}).get("configurable", {})
    session_id = configuravel.get("user_id") or configuravel.get("thread_id")

    if not session_id:
        return "Não foi possível identificar a sessão para buscar o histórico."

    resumos = buscar_resumos(session_id, busca=busca, limite=3)

    if not resumos:
        return "Nenhuma conversa anterior relevante encontrada."

    return "\n\n".join(
        f"[{r['encerrada_em']:%d/%m/%Y}] {r['resumo']}" for r in resumos
    )


TOOLS_MEMORIA = [buscar_historico]
