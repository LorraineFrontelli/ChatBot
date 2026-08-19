from pymongo import MongoClient

from app.core.config.settings import settings

_client: MongoClient | None = None


def get_mongodb_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2000)
    return _client
