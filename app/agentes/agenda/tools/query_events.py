import logging
from typing import Optional

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from app.infra.database.postgres_client import get_cursor

logger = logging.getLogger(__name__)


class QueryEventsArgs(BaseModel):
    text: Optional[str] = Field(
        default=None,
        description="Texto para busca em title, location, notes OU source_text (ex.: 'dentista', 'Marcos').",
    )
    date_local: Optional[str] = Field(
        default=None,
        description="Data local (YYYY-MM-DD) em America/Sao_Paulo para filtrar o dia.",
    )
    date_from_local: Optional[str] = Field(
        default=None, description="Data local inicial (YYYY-MM-DD) inclusive."
    )
    date_to_local: Optional[str] = Field(
        default=None, description="Data local final (YYYY-MM-DD) inclusive."
    )
    limit: int = Field(
        default=20, ge=1, le=200, description="Máximo de registros retornados (1..200)."
    )


@tool("query_events", args_schema=QueryEventsArgs)
def query_events(
    config: RunnableConfig,
    text: Optional[str] = None,
    date_local: Optional[str] = None,
    date_from_local: Optional[str] = None,
    date_to_local: Optional[str] = None,
    limit: int = 20,
) -> dict:
    """
    Consulta eventos da agenda (tabela events) com filtros por texto e datas locais (America/Sao_Paulo).
    Use esta tool ANTES de confirmar disponibilidade ou conflito.
    Ordenação cronológica ascendente por start_time.
    Use date_local OU (date_from_local/date_to_local), nunca ambos.
    """
    logger.info("query_events tool called")
    user_id = (config or {}).get("configurable", {}).get("user_id")
    if user_id is None:
        logger.error("query_events chamada sem user_id no config")
        return {"status": "error", "message": "Não foi possível identificar o usuário."}
    if date_local and (date_from_local or date_to_local):
        return {"status": "error", "message": "Use date_local OU (date_from_local/date_to_local), não ambos."}
    try:
        where_sql = "WHERE e.user_id = %(user_id)s"
        params: dict = {"user_id": user_id, "limit": limit}

        if text:
            where_sql += (
                " AND (e.title ILIKE %(text_like)s"
                " OR e.location ILIKE %(text_like)s"
                " OR e.notes ILIKE %(text_like)s"
                " OR e.source_text ILIKE %(text_like)s)"
            )
            params["text_like"] = f"%{text}%"

        if date_local:
            where_sql += (
                " AND e.start_time >= (%(date_local)s::date AT TIME ZONE 'America/Sao_Paulo')"
                " AND e.start_time < ((%(date_local)s::date + INTERVAL '1 day') AT TIME ZONE 'America/Sao_Paulo')"
            )
            params["date_local"] = date_local
        else:
            if date_from_local:
                where_sql += " AND e.start_time >= (%(date_from)s::date AT TIME ZONE 'America/Sao_Paulo')"
                params["date_from"] = date_from_local
            if date_to_local:
                where_sql += " AND e.start_time < ((%(date_to)s::date + INTERVAL '1 day') AT TIME ZONE 'America/Sao_Paulo')"
                params["date_to"] = date_to_local

        sql = f"""
            SELECT e.id, e.title, e.start_time, e.end_time, e.location, e.notes, e.source_text, e.recorded_at
            FROM events e
            {where_sql}
            ORDER BY e.start_time ASC
            LIMIT %(limit)s;
        """
        with get_cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        logger.info("Result size: %s", len(rows))

        results = [
            {
                "id": r[0],
                "title": r[1],
                "start_time": str(r[2]),
                "end_time": str(r[3]) if r[3] else None,
                "location": r[4],
                "notes": r[5],
                "source_text": r[6],
                "recorded_at": str(r[7]),
            }
            for r in rows
        ]
        return {"status": "ok", "count": len(results), "results": results}

    except Exception as e:
        logger.exception("Exception raised while querying events")
        return {"status": "error", "message": str(e)}
