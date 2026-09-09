from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """O que o navegador envia no POST /register."""
    nome: str = Field(..., min_length=1, examples=["Lorraine"])
    email: EmailStr
    senha: str = Field(..., examples=["minhasenha123"])

    @field_validator("senha")
    @classmethod
    def valida_senha(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("senha precisa ter no mínimo 8 caracteres")
        return v


class UserOut(BaseModel):
    """O que a API devolve no POST /register."""
    id:    int
    nome:  str
    email: EmailStr


class LoginRequest(BaseModel):
    """O que o navegador envia no POST /login."""
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    """O que a API devolve no POST /login."""
    access_token: str
    token_type:   str = "bearer"


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