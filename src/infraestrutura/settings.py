from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    gemini_api_key: str
    groq_api_key: str

    db_port: Optional[str] = None
    pguser: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_db: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self):
        missing = [
            name
            for name in ("pguser", "postgres_password", "postgres_db", "db_port")
            if not getattr(self, name)
        ]
        if missing:
            raise ValueError(
                "Variaveis do PostgreSQL ausentes no .env: "
                + ", ".join(missing)
            )
        return f"postgresql://{self.pguser}:{self.postgres_password}@localhost:{self.db_port}/{self.postgres_db}"


settings = Settings()
