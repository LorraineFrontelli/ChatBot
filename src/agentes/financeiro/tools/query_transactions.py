import logging
from typing import Optional
from datetime import date

from langchain.tools import tool
from pydantic import BaseModel, Field

from src.infraestrutura.db_connection import get_cursor
from src.agentes.financeiro.tools.utils import resolve_type_id, resolve_category_id

logger = logging.getLogger(__name__)


class QueryTransactionsArgs(BaseModel):
    source_text: Optional[str] = Field(
        default=None,
        description="Texto original da mensagem do usuário que gerou o registro.",
    )
    occurred_at_start: Optional[date] = Field(
        default=None,
        description="Data de início do intervalo de datas de transações alvo.",
    )
    occurred_at_end: Optional[date] = Field(
        default=None,
        description=(
            "Data de término do intervalo (excludente). "
            "OBRIGATÓRIO SE o usuário mencionar um período com fim definido "
            "(ex: 'mês passado', 'semana passada', 'em março', 'no ano passado'). "
            "Exemplo: para 'mês passado' em abril/2026, passe 2026-04-01."
        ),
    )
    type_name: Optional[str] = Field(
        default=None,
        description="Nome do tipo: INCOME | EXPENSES | TRANSFER.",
    )
    category: Optional[str] = Field(
        default=None,
        description="Nome da categoria: comida | besteira | estudo | férias | transporte | moradia | saúde | lazer | contas | investimento | presente | outros.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Descrição da transação.",
    )
    limit: Optional[str] = Field(
        default="50",
        description="Número máximo de transações. Use 0 para sem limite.",
    )


@tool("query_transactions", args_schema=QueryTransactionsArgs)
def query_transactions(
    source_text: Optional[str] = None,
    occurred_at_start: Optional[date] = None,
    occurred_at_end: Optional[date] = None,
    type_name: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    limit: str = "50",
) -> dict:
    """
    Busca no banco de dados transações de acordo com os parâmetros passados.
    Caso nenhum parâmetro seja passado, retorna as últimas 50 transações.
    Buscas por source_text ou description fazem busca parcial.
    Se a data de início for passada mas a de final não, retorna todas desde o início até hoje.
    Se a data de início não for passada mas a de final for, retorna todas até a data de final.
    """
    logger.info("query_transactions tool called")
    try:
        limit_int = int(limit)
        if limit_int < 0:
            return {"status": "error", "message": "Limite inválido. Deve ser >= 0."}

        with get_cursor() as cur:
            query = """
                SELECT
                    t.id,
                    t.amount,
                    tt.type,
                    c.name AS category,
                    t.description,
                    t.payment_method,
                    t.source_text,
                    t.occurred_at
                FROM transactions t
                JOIN transaction_types tt ON tt.id = t.type
                LEFT JOIN categories c ON c.id = t.category_id
                WHERE 1=1
            """
            params = []

            if source_text:
                query += " AND t.source_text ILIKE %s"
                params.append(f"%{source_text}%")

            if description:
                query += " AND t.description ILIKE %s"
                params.append(f"%{description}%")

            if type_name:
                type_id = resolve_type_id(cur, None, type_name)
                if not type_id:
                    return {"status": "error", "message": f"Tipo inválido: {type_name}"}
                query += " AND t.type = %s"
                params.append(type_id)

            if category:
                category_id = resolve_category_id(cur, None, category)
                if not category_id:
                    return {"status": "error", "message": f"Categoria inválida: {category}"}
                query += " AND t.category_id = %s"
                params.append(category_id)

            if occurred_at_start:
                query += " AND t.occurred_at >= %s"
                params.append(occurred_at_start)

            if occurred_at_end:
                query += " AND t.occurred_at < %s"
                params.append(occurred_at_end)

            order = "ASC" if (occurred_at_start or occurred_at_end) else "DESC"
            query += f" ORDER BY t.occurred_at {order}"

            if limit_int > 0:
                query += " LIMIT %s"
                params.append(limit_int)

            query += ";"
            logger.debug("Final query: %s", query)

            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            logger.info("Result size: %s", len(rows))

            transactions = [
                {
                    "id": r[0],
                    "amount": float(r[1]),
                    "type": r[2],
                    "category": r[3],
                    "description": r[4],
                    "payment_method": r[5],
                    "source_text": r[6],
                    "occurred_at": str(r[7]),
                }
                for r in rows
            ]

            return {"status": "ok", "transactions": transactions}

    except Exception as e:
        logger.exception("Exception raised while querying transactions")
        return {"status": "error", "message": str(e)}