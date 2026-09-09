import logging
from datetime import date, timedelta

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from app.infra.database.postgres_client import get_cursor

logger = logging.getLogger(__name__)


class DailyBalanceArgs(BaseModel):
    target_date: date = Field(
        ...,
        description=(
            "Data de referência para o cálculo do saldo. "
            "O saldo retornado será o acumulado de todas as entradas (INCOME) "
            "e saídas (EXPENSES), ignorando transferências (TRANSFER) "
            "registradas ATÉ esse dia (inclusive). "
            "Exemplos: 'qual meu saldo hoje' → {hoje}, "
            "'qual era meu saldo no fim de março' → 2026-03-31."
        ),
    )


@tool("daily_balance", args_schema=DailyBalanceArgs)
def daily_balance(target_date: date, config: RunnableConfig) -> dict:
    """
    Retorna o saldo (INCOME - EXPENSES) do dia local informado em America/Sao_Paulo.
    Ignora TRANSFER (type=3)
    """
    logger.info("daily_balance tool called")
    user_id = (config or {}).get("configurable", {}).get("user_id")
    if user_id is None:
        logger.error("daily_balance chamada sem user_id no config")
        return {"status": "error", "message": "Não foi possível identificar o usuário."}
    query_date = target_date + timedelta(days=1)
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT coalesce(sum(amount), 0) FROM transactions WHERE type = 1 AND occurred_at < %s AND user_id = %s",
                (query_date, user_id),
            )
            income = cur.fetchone()[0]
            logger.debug("Retrieved income: %s", income)

            cur.execute(
                "SELECT coalesce(sum(amount), 0) FROM transactions WHERE type = 2 AND occurred_at < %s AND user_id = %s",
                (query_date, user_id),
            )
            expenses = cur.fetchone()[0]
            logger.debug("Retrieved expenses: %s", expenses)

            balance = income - expenses
            logger.info("Daily balance retrieved successfully: %s", balance)
            return {"status": "ok", "saldo_diario": float(balance)}

    except Exception as e:
        logger.exception("Exception raised while retrieving daily balance")
        return {"status": "error", "message": str(e)}