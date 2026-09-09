"""Acesso à tabela `users` no Postgres."""

from app.infra.database.postgres_client import get_cursor


def criar_usuario(nome: str, email: str, senha_hash: str) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (nome, email, senha_hash)
            VALUES (%s, %s, %s)
            RETURNING id, nome, email;
            """,
            (nome, email, senha_hash),
        )
        row = cur.fetchone()
        return {"id": row[0], "nome": row[1], "email": row[2]}


def buscar_usuario_por_email(email: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, nome, email, senha_hash FROM users WHERE email = %s;",
            (email,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "nome": row[1], "email": row[2], "senha_hash": row[3]}
