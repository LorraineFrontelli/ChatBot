"""Conexão com o Postgres para as tools financeiras, via pool"""

from contextlib import contextmanager

from psycopg2 import pool

from app.core.config.settings import settings

_pool: pool.ThreadedConnectionPool | None = None


def _get_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = pool.ThreadedConnectionPool(
            minconn=1, maxconn=10, dsn=settings.DATABASE_URL
        )
    return _pool


@contextmanager
def get_cursor():
    """Empresta uma conexão do pool, entrega um cursor, devolve ao sair."""
    conn = _get_pool().getconn()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _get_pool().putconn(conn)
