from datetime import datetime, timezone

from app.core.config.settings import settings
from app.infra.database.mongodb_client import get_mongodb_client

_COLLECTION = "mensagens"


def _collection():
    db = get_mongodb_client()[settings.MONGODB_DB]
    col = db[_COLLECTION]
    col.create_index("session_id")
    col.create_index("timestamp")
    col.create_index([("user_id", 1), ("session_id", 1)])
    return col


def salvar_mensagem(
    session_id: str,
    user_id: int,
    role: str,
    content: str,
    agentes_chamados: list[str] | None = None,
) -> None:
    """`user_id` é campo de primeira classe aqui, não algo pra deduzir depois
    fazendo parse do thread_id do LangGraph — vem sempre de
    config["configurable"]["user_id"]/get_current_user_id, nunca do corpo
    da requisição."""
    doc = {
        "session_id": session_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc),
    }
    if agentes_chamados:
        doc["agentes_chamados"] = agentes_chamados
    _collection().insert_one(doc)


def recuperar_historico(session_id: str, limite: int = 8) -> list[dict]:
    docs = _collection().find({"session_id": session_id}).sort("timestamp", -1).limit(limite)
    return list(reversed(list(docs)))


def recuperar_mensagens_desde(session_id: str, desde: datetime | None) -> list[dict]:
    """Todas as mensagens da sessão a partir de `desde` (exclusive), em ordem
    cronológica. `desde=None` traz o histórico inteiro da sessão."""
    filtro: dict = {"session_id": session_id}
    if desde is not None:
        filtro["timestamp"] = {"$gt": desde}
    return list(_collection().find(filtro).sort("timestamp", 1))


def timestamp_ultima_mensagem(session_id: str) -> datetime | None:
    doc = _collection().find_one({"session_id": session_id}, sort=[("timestamp", -1)])
    return doc["timestamp"] if doc else None
