from fastapi import APIRouter

from app.memory.log.session_summary import gerar_resumo_sessao
from app.schemas import EncerrarSessaoRequest, SessionResponse

router = APIRouter(tags=["session"])


@router.post("/session/end", response_model=SessionResponse)
def encerrar_sessao(requisicao: EncerrarSessaoRequest) -> SessionResponse:
    """Encerramento explícito — chamado pelo botão "nova sessão" e por
    sendBeacon quando a aba fecha. É o caminho feliz; quem não passar por
    aqui ainda é coberto pela detecção de inatividade em app/routes/chat.py.
    """
    resumo = gerar_resumo_sessao(requisicao.session_id, motivo="explicita")
    return SessionResponse(session_id=requisicao.session_id, resumo=resumo)
