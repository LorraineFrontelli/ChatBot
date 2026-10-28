import logging
from typing import Optional

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from app.infra.database.postgres_client import get_cursor

logger = logging.getLogger(__name__)


class AddEventArgs(BaseModel):
    title: str = Field(..., description="Título do evento.")
    source_text: str = Field(..., description="Texto original do usuário.")
    start_time: str = Field(
        ...,
        description="Início do evento em ISO 8601 com fuso (ex.: '2026-09-10T14:00:00-03:00'). Obrigatório.",
    )
    end_time: Optional[str] = Field(
        default=None, description="Fim do evento em ISO 8601 com fuso. Opcional."
    )
    location: Optional[str] = Field(
        default=None, description="Local do evento (ex.: 'Sala 3', 'Zoom', 'Rua X, 100')."
    )
    notes: Optional[str] = Field(
        default=None, description="Observações adicionais sobre o evento."
    )


@tool("add_event", args_schema=AddEventArgs)
def add_event(
    title: str,
    source_text: str,
    start_time: str,
    config: RunnableConfig,
    end_time: Optional[str] = None,
    location: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """Insere um evento/compromisso na agenda (tabela events) do banco de dados Postgres."""
    logger.info("add_event tool called")
    user_id = (config or {}).get("configurable", {}).get("user_id")
    if user_id is None:
        logger.error("add_event chamada sem user_id no config")
        return {"status": "error", "message": "Não foi possível identificar o usuário."}
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO events
                    (title, start_time, end_time, location, notes, source_text, user_id)
                VALUES
                    (%s, %s::timestamptz, %s::timestamptz, %s, %s, %s, %s)
                RETURNING id, start_time, end_time;
                """,
                (title, start_time, end_time, location, notes, source_text, user_id),
            )
            new_id, start, end = cur.fetchone()
            logger.info("Event added successfully: id=%s", new_id)
            return {
                "status": "ok",
                "id": new_id,
                "title": title,
                "start_time": str(start),
                "end_time": str(end) if end else None,
            }

    except Exception as e:
        logger.exception("Exception raised while trying to add event to database")
        return {"status": "error", "message": str(e)}
