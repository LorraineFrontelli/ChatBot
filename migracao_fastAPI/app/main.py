from fastapi import FastAPI
from app.routes import chat
from app.config import validar_config          

app = FastAPI(
    title="Assessor IA",
    description="Assessor financeiro e de agenda com LanghChain e LanghGraph.",
    version="0.1.0"
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