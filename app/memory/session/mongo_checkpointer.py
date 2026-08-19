from langgraph.checkpoint.mongodb import MongoDBSaver

from app.core.config.settings import settings
from app.infra.database.mongodb_client import get_mongodb_client


def get_checkpointer() -> MongoDBSaver:
    """MongoDBSaver.from_conn_string() devolve um context manager (fecha a
    conexão ao sair do `with`) — não serve pra um checkpointer que precisa
    ficar vivo durante toda a vida do servidor. Por isso construímos direto
    com um client normal."""
    return MongoDBSaver(client=get_mongodb_client(), db_name=settings.MONGODB_DB)
