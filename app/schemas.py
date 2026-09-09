from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


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


class PerfilRequest(BaseModel):
    """O que a tela Perfil envia no POST /perfil.

    `user_id` vem do corpo mesmo (e não de um token, como em /chat): esta
    rota não tem autenticação, é o contrato explícito da prova. Salvar de
    novo com o mesmo user_id substitui o cadastro inteiro, restrições
    incluídas — não é um PATCH incremental."""
    user_id:            str = Field(..., min_length=1, examples=["usuario_teste"])
    renda_mensal:        float = Field(..., gt=0, examples=[6000])
    gasto_fixo_mensal:   float = Field(..., ge=0, examples=[3800])
    horizonte_meses:     int = Field(..., ge=1, le=120, examples=[18])
    perfil_investidor:   Literal["conservador", "moderado", "arrojado"]
    restricoes:          list[str] = Field(..., min_length=1, max_length=5)

    @field_validator("restricoes")
    @classmethod
    def valida_restricoes(cls, v: list[str]) -> list[str]:
        limpas = [texto.strip() for texto in v]
        if any(texto == "" for texto in limpas):
            raise ValueError("restrições não podem ser vazias")
        return limpas

    @model_validator(mode="after")
    def valida_gasto_menor_que_renda(self) -> "PerfilRequest":
        if self.gasto_fixo_mensal >= self.renda_mensal:
            raise ValueError("gasto_fixo_mensal precisa ser menor que renda_mensal")
        return self


class PerfilResponse(PerfilRequest):
    """O que a API devolve no POST /perfil: o perfil que ficou salvo."""