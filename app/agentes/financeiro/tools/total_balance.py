import logging

from langchain.tools import tool

from app.infra.database.postgres_client import get_cursor

logger = logging.getLogger(__name__)


@tool("total_balance")
def total_balance() -> dict:
    """Recupera do banco de dados o saldo atual a partir de todas as transações registradas"""
    logger.info("total_balance tool called")
    try:
        with get_cursor() as cur:
            cur.execute("SELECT coalesce(sum(amount), 0) FROM transactions WHERE type = 1")
            income = cur.fetchone()[0]
            logger.debug("Income retrieved: %s", income)

            cur.execute("SELECT coalesce(sum(amount), 0) FROM transactions WHERE type = 2")
            expenses = cur.fetchone()[0]
            logger.debug("Expenses retrieved: %s", expenses)

            balance = income - expenses
            logger.info("Total balance retrieved successfully: %s", balance)
            return {"status": "ok", "saldo": float(balance)}

    except Exception as e:
        logger.exception("Exception raised while retrieving total balance")
        return {"status": "error", "message": str(e)}