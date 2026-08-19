from datetime import datetime, timezone

from app.core.config.settings import settings
from app.infra.database.mongodb_client import get_mongodb_client

_COLLECTION = "mensagens"


def _collection():
    db = get_mongodb_client()[settings.MONGODB_DB]
    col = db[_COLLECTION]
    col.create_index("session_id")
    col.create_index("timestamp")
    return col


def salvar_mensagem(session_id: str, role: str, content: str) -> None:
    _collection().insert_one({
        "session_id": session_id,
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc),
    })


def recuperar_historico(session_id: str, limite: int = 8) -> list[dict]:
    docs = _collection().find({"session_id": session_id}).sort("timestamp", -1).limit(limite)
    return list(reversed(list(docs)))
