"""Perfil financeiro — parte estruturada (renda, gasto fixo, horizonte,
perfil de investidor), guardada no Mongo. O texto livre (`restricoes`) não
mora aqui: fica no Qdrant (ver restricoes_repo.py), porque precisa de busca
semântica, não de consulta direta por campo.

`user_id` chega como string (é o contrato do POST /perfil, sem autenticação
— ver JUSTIFICATIVA.md) e é gravado exatamente como chegou.
"""
from datetime import datetime, timezone

from app.core.config.settings import settings
from app.infra.database.mongodb_client import get_mongodb_client

_COLLECTION = "perfis"


def _collection():
    db = get_mongodb_client()[settings.MONGODB_DB]
    col = db[_COLLECTION]
    col.create_index("user_id", unique=True)
    return col


def salvar_perfil(
    user_id: str,
    renda_mensal: float,
    gasto_fixo_mensal: float,
    horizonte_meses: int,
    perfil_investidor: str,
) -> dict:
    """Upsert por user_id: salvar de novo substitui o documento inteiro, não
    faz merge de campo a campo — não sobra dado velho de um cadastro anterior."""
    doc = {
        "user_id": user_id,
        "renda_mensal": renda_mensal,
        "gasto_fixo_mensal": gasto_fixo_mensal,
        "horizonte_meses": horizonte_meses,
        "perfil_investidor": perfil_investidor,
        "updated_at": datetime.now(timezone.utc),
    }
    _collection().replace_one({"user_id": user_id}, doc, upsert=True)
    return doc


def buscar_perfil(user_id: str) -> dict | None:
    """None quando o usuário nunca cadastrou perfil — quem chama (a tool do
    especialista) não pode inventar números nesse caso, só orientar a
    preencher a tela Perfil."""
    return _collection().find_one({"user_id": user_id})
