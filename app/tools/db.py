import psycopg2

from app.core.config.settings import settings

def get_conn():
    """Retorna uma conexão com o banco de dados PostgreSQL."""
    return psycopg2.connect(settings.DATABASE_URL)