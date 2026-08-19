"""Conexão com o Postgres para as tools financeiras."""

from contextlib import contextmanager

import psycopg2

from app.core.config.settings import settings


@contextmanager
def get_cursor():
    """Abre uma conexão, entrega um cursor, comita ao sair, sempre fecha."""
    conn = psycopg2.connect(settings.DATABASE_URL)
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
