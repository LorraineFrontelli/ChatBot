import logging

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig

from app.agentes.financeiro.perfil import buscar_perfil

logger = logging.getLogger(__name__)


@tool("consultar_perfil_financeiro")
def consultar_perfil_financeiro(config: RunnableConfig) -> dict:
    """Recupera o cadastro financeiro do usuário: renda mensal, gasto fixo
    mensal, horizonte de tempo (em meses) e perfil de investidor
    (conservador, moderado ou arrojado).

    Use ANTES de recomendar quanto guardar/investir por mês, ou qualquer
    conselho que dependa de quanto o usuário ganha, gasta ou por quanto
    tempo pretende deixar o dinheiro aplicado. Se o retorno for
    status "not_found", NÃO invente nenhum número: oriente o usuário a
    preencher a tela Perfil — este cadastro só é feito por lá."""
    logger.info("consultar_perfil_financeiro tool called")
    user_id = (config or {}).get("configurable", {}).get("user_id")
    if user_id is None:
        logger.error("consultar_perfil_financeiro chamada sem user_id no config")
        return {"status": "error", "message": "Não foi possível identificar o usuário."}

    perfil = buscar_perfil(str(user_id))
    if perfil is None:
        return {
            "status": "not_found",
            "message": "Usuário ainda não cadastrou o perfil financeiro na tela Perfil.",
        }

    return {
        "status": "ok",
        "renda_mensal": perfil["renda_mensal"],
        "gasto_fixo_mensal": perfil["gasto_fixo_mensal"],
        "horizonte_meses": perfil["horizonte_meses"],
        "perfil_investidor": perfil["perfil_investidor"],
    }
