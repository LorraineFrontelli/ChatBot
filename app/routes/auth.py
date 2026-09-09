import logging

from fastapi import APIRouter, HTTPException, status

from app.infra.database.users_repo import buscar_usuario_por_email, criar_usuario
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserOut
from app.security import criar_token, hash_senha, verifica_senha

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(usuario: UserCreate) -> UserOut:
    if buscar_usuario_por_email(usuario.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "email já cadastrado")

    novo = criar_usuario(usuario.nome, usuario.email, hash_senha(usuario.senha))
    logger.info("Usuário registrado: id=%s", novo["id"])
    return UserOut(**novo)


@router.post("/login", response_model=TokenResponse)
def login(credenciais: LoginRequest) -> TokenResponse:
    usuario = buscar_usuario_por_email(credenciais.email)
    if not usuario or not verifica_senha(credenciais.senha, usuario["senha_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "credenciais inválidas")

    token = criar_token(usuario["id"])
    return TokenResponse(access_token=token)
