from pymongo import MongoClient

from app.core.config.settings import settings

_client: MongoClient | None = None


def get_mongodb_client() -> MongoClient:
    """tz_aware=True porque o pymongo, por padrão, devolve datetime *naive*
    (sem tzinfo) na leitura — mesmo pra valores gravados em UTC. Sem isso,
    comparar um horário lido do Mongo com datetime.now(timezone.utc) quebra
    com 'can't subtract offset-naive and offset-aware datetimes'."""
    global _client
    if _client is None:
        _client = MongoClient(
            settings.MONGODB_URI, serverSelectionTimeoutMS=2000, tz_aware=True
        )
    return _client
