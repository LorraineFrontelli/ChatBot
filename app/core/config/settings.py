"""Único ponto de leitura do .env do projeto."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
FAQ_PDF_PATH = DATA_DIR / "FAQ_assessor_v1.1.pdf"


class Settings(BaseSettings):
    GEMINI_API_KEY: str
    GROQ_API_KEY: str
    DATABASE_URL: str
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "assessor"
    SESSION_IDLE_MINUTES: int = 30
    QDRANT_URL: str
    QDRANT_API_KEY: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 60 * 24
    MCP_USER_ID: int | None = None
    GOOGLE_OAUTH_CREDENTIALS: str = "gcp-oauth.keys.json"
    GOOGLE_CALENDAR_MCP_URL: str = "https://calendarmcp.googleapis.com/mcp/v1"
    GOOGLE_CALENDAR_ACCESS_TOKEN: str = ""
    # Juiz de fidelidade (JEV, TypeSafe): opcional. Sem a chave, o juiz
    # troca toda resposta pela frase fixa ([juiz] sem_chave).
    TYPESAFE_API_KEY: str = ""
    # LangSmith (opcional): sem a chave, o tracing fica desligado e o app
    # funciona igual.
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "assessor-aula"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")


settings = Settings()

# O pydantic-settings lê o .env só para preencher `settings`, sem exportar
# para os.environ. O LangChain/LangSmith lê estas três direto do ambiente,
# então elas são repassadas daqui. Não sobrescreve o que já estiver no ambiente.
if settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY:
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_API_KEY", settings.LANGSMITH_API_KEY)
    os.environ.setdefault("LANGSMITH_PROJECT", settings.LANGSMITH_PROJECT)


def validar_config() -> list[str]:
    """As chaves obrigatórias já são validadas pelo pydantic-settings na
    criação de `settings` — se faltarem, o processo nem sobe. Esta função
    cobre só o que o pydantic não valida sozinho: a existência do PDF."""
    problemas = []
    if not FAQ_PDF_PATH.exists():
        problemas.append(f"PDF do FAQ não encontrado em: {FAQ_PDF_PATH}")
    return problemas
