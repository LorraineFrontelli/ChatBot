import re

_ROUTE_PATTERN = re.compile(r"(?<=ROUTE=)\w+")
ROTAS_VALIDAS = {"financeiro", "agenda", "faq"}


def match_agent(texto: str) -> str | None:
    match = _ROUTE_PATTERN.search(texto)
    return match.group() if match else None


def decidir_pos_guardrail_entrada(state) -> str:
    return "fim" if state.get("rota") == "bloqueado" else "router"


def decidir_pos_router(state) -> str:
    rota = state.get("rota")
    return rota if rota in ROTAS_VALIDAS else "guardrail_saida"
