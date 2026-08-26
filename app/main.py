from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config.settings import validar_config
from app.routes import chat, session

app = FastAPI(
    title="Assessor IA",
    description="Assessor financeiro e de agenda com LanghChain e LanghGraph.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # em produção, trocar "*" pela URL real do frontend
    allow_methods=["*"],
    allow_headers=["*"],
)

for _problema in validar_config():                 # logo antes de app = FastAPI(...)
    print(f"[config] ATENÇÃO: {_problema}")

@app.get("/health")
def health() -> dict:
    problemas = validar_config()
    return {
        "status": "ok" if not problemas else "atencao",
        "problemas_de_configuracao": problemas,
    }

app.include_router(chat.router)
app.include_router(session.router)

# Precisa vir por último: é um catch-all em "/", se viesse antes
# interceptaria as rotas /health e /chat.
app.mount("/", StaticFiles(directory="app/frontend", html=True), name="frontend")
