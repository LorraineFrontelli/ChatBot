import sys
from pathlib import Path
from typing import Annotated, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from app.agentes.agenda.tools import add_event as _add_event
from app.agentes.agenda.tools import query_events as _query_events
from app.agentes.financeiro.tools import (
    add_transaction as _add_transaction,
    daily_balance as _daily_balance,
    query_transactions as _query_transactions,
    total_balance as _total_balance,
    update_transaction as _update_transaction,
)
from app.core.config.settings import settings

mcp = MCPServer(
    name="assessor-financeiro",
    version="1.0.0",
    instructions=(
        "Ferramentas do Assessor.AI: finanças (saldo, lançamentos) e agenda (eventos) "
        "do usuário configurado em MCP_USER_ID."
    ),
)

LEITURA = ToolAnnotations(readOnlyHint=True)
ESCRITA = ToolAnnotations(readOnlyHint=False, destructiveHint=False)


def _invocar(ferramenta, argumentos: dict[str, Any]) -> dict[str, Any]:
    if settings.MCP_USER_ID is None:
        return {"status": "error", "message": "MCP_USER_ID ausente no .env."}
    config = {"configurable": {"user_id": settings.MCP_USER_ID}}
    return ferramenta.invoke(argumentos, config=config)


@mcp.tool(
    name="total_balance",
    title="Saldo total",
    description="Saldo de todo o histórico: receitas menos despesas.",
    annotations=LEITURA,
)
def total_balance() -> dict[str, Any]:
    return _invocar(_total_balance, {})


@mcp.tool(
    name="daily_balance",
    title="Saldo até uma data",
    description="Saldo acumulado (receitas menos despesas, sem transferências) até o dia informado, inclusive.",
    annotations=LEITURA,
)
def daily_balance(
    target_date: Annotated[str, Field(description="Data no formato YYYY-MM-DD.")],
) -> dict[str, Any]:
    return _invocar(_daily_balance, {"target_date": target_date})


@mcp.tool(
    name="query_transactions",
    title="Consultar transações",
    description="Lista transações com filtros opcionais de texto, tipo, categoria e datas.",
    annotations=LEITURA,
)
def query_transactions(
    source_text: Annotated[Optional[str], Field(description="Trecho do texto original (busca parcial).")] = None,
    description: Annotated[Optional[str], Field(description="Trecho da descrição (busca parcial).")] = None,
    type_name: Annotated[Optional[str], Field(description="INCOME | EXPENSES | TRANSFER")] = None,
    category: Annotated[Optional[str], Field(description="Categoria em pt-BR (ex.: comida, férias).")] = None,
    occurred_at_start: Annotated[Optional[str], Field(description="Início do intervalo, YYYY-MM-DD.")] = None,
    occurred_at_end: Annotated[Optional[str], Field(description="Fim do intervalo (excludente), YYYY-MM-DD.")] = None,
    limit: Annotated[int, Field(description="Máximo de registros; 0 = sem limite.", ge=0)] = 50,
) -> dict[str, Any]:
    return _invocar(
        _query_transactions,
        {
            "source_text": source_text,
            "description": description,
            "type_name": type_name,
            "category": category,
            "occurred_at_start": occurred_at_start,
            "occurred_at_end": occurred_at_end,
            "limit": str(limit),
        },
    )


@mcp.tool(
    name="add_transaction",
    title="Registrar transação",
    description="Registra uma transação na tabela transactions.",
    annotations=ESCRITA,
)
def add_transaction(
    amount: Annotated[float, Field(description="Valor (sempre positivo).")],
    source_text: Annotated[str, Field(description="Texto original do pedido.")],
    type_name: Annotated[Optional[str], Field(description="INCOME | EXPENSES | TRANSFER")] = None,
    category_name: Annotated[Optional[str], Field(description="Categoria em pt-BR.")] = None,
    description: Annotated[Optional[str], Field(description="Descrição.")] = None,
    payment_method: Annotated[Optional[str], Field(description="Forma de pagamento.")] = None,
    occurred_at: Annotated[Optional[str], Field(description="Data/hora ISO 8601; vazio = agora.")] = None,
) -> dict[str, Any]:
    return _invocar(
        _add_transaction,
        {
            "amount": amount,
            "source_text": source_text,
            "type_name": type_name,
            "category_name": category_name or "outros",
            "description": description,
            "payment_method": payment_method,
            "occurred_at": occurred_at,
        },
    )


@mcp.tool(
    name="update_transaction",
    title="Atualizar transação",
    description="Atualiza uma transação por id, ou por match_text + date_local quando o id não é conhecido.",
    annotations=ESCRITA,
)
def update_transaction(
    id: Annotated[Optional[int], Field(description="ID da transação.")] = None,
    match_text: Annotated[Optional[str], Field(description="Texto para localizar quando não há id.")] = None,
    date_local: Annotated[Optional[str], Field(description="Data local YYYY-MM-DD, junto com match_text.")] = None,
    amount: Annotated[Optional[float], Field(description="Novo valor.")] = None,
    type_name: Annotated[Optional[str], Field(description="INCOME | EXPENSES | TRANSFER")] = None,
    category_name: Annotated[Optional[str], Field(description="Nova categoria em pt-BR.")] = None,
    description: Annotated[Optional[str], Field(description="Nova descrição.")] = None,
    payment_method: Annotated[Optional[str], Field(description="Nova forma de pagamento.")] = None,
    occurred_at: Annotated[Optional[str], Field(description="Nova data/hora ISO 8601.")] = None,
) -> dict[str, Any]:
    return _invocar(
        _update_transaction,
        {
            "id": id,
            "match_text": match_text,
            "date_local": date_local,
            "amount": amount,
            "type_name": type_name,
            "category_name": category_name,
            "description": description,
            "payment_method": payment_method,
            "occurred_at": occurred_at,
        },
    )


@mcp.tool(
    name="query_events",
    title="Consultar agenda",
    description="Lista eventos da agenda com filtros de texto e de datas locais (America/Sao_Paulo).",
    annotations=LEITURA,
)
def query_events(
    text: Annotated[Optional[str], Field(description="Busca em título, local, notas e texto original.")] = None,
    date_local: Annotated[Optional[str], Field(description="Um dia, YYYY-MM-DD.")] = None,
    date_from_local: Annotated[Optional[str], Field(description="Início inclusive, YYYY-MM-DD.")] = None,
    date_to_local: Annotated[Optional[str], Field(description="Fim inclusive, YYYY-MM-DD.")] = None,
    limit: Annotated[int, Field(description="Máximo de registros (1 a 200).", ge=1, le=200)] = 20,
) -> dict[str, Any]:
    return _invocar(
        _query_events,
        {
            "text": text,
            "date_local": date_local,
            "date_from_local": date_from_local,
            "date_to_local": date_to_local,
            "limit": limit,
        },
    )


@mcp.tool(
    name="add_event",
    title="Registrar evento",
    description="Registra um evento na tabela events (somente banco, não grava no Google Calendar).",
    annotations=ESCRITA,
)
def add_event(
    title: Annotated[str, Field(description="Título do evento.")],
    source_text: Annotated[str, Field(description="Texto original do pedido.")],
    start_time: Annotated[str, Field(description="Início em ISO 8601 com fuso, ex.: 2026-10-30T15:00:00-03:00.")],
    end_time: Annotated[Optional[str], Field(description="Fim em ISO 8601 com fuso.")] = None,
    location: Annotated[Optional[str], Field(description="Local.")] = None,
    notes: Annotated[Optional[str], Field(description="Observações.")] = None,
) -> dict[str, Any]:
    return _invocar(
        _add_event,
        {
            "title": title,
            "source_text": source_text,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "notes": notes,
        },
    )


if __name__ == "__main__":
    if settings.MCP_USER_ID is None:
        print("[assessor-financeiro] MCP_USER_ID ausente no .env", file=sys.stderr)
    mcp.run(transport="stdio")
