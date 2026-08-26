from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """O que o navegador envia no POST /chat"""
    session_id: str = Field(..., examples=["id_usuario"])
    pergunta: str = Field(..., min_length=1, examples=["Gastei 50 reais no mercado"])

class ChatResponse(BaseModel):
    """O que a API devolve no POST /chat."""
    resposta:         str
    agentes_chamados: list[str] = Field(default_factory=list)


class EncerrarSessaoRequest(BaseModel):
    """O que o navegador envia no POST /session/end."""
    session_id: str = Field(..., examples=["id_usuario"])


class SessionResponse(BaseModel):
    """O que a API devolve no POST /session/end."""
    session_id: str
    resumo:     str | None = None