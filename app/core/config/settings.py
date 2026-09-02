"""Único ponto de leitura do .env do projeto."""

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

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")


settings = Settings()


def validar_config() -> list[str]:
    """As chaves obrigatórias já são validadas pelo pydantic-settings na
    criação de `settings` — se faltarem, o processo nem sobe. Esta função
    cobre só o que o pydantic não valida sozinho: a existência do PDF."""
    problemas = []
    if not FAQ_PDF_PATH.exists():
        problemas.append(f"PDF do FAQ não encontrado em: {FAQ_PDF_PATH}")
    return problemas
