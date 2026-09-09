from fastapi import APIRouter

from app.memory.log.session_summary import gerar_resumo_sessao
from app.schemas import EncerrarSessaoRequest, SessionResponse

router = APIRouter(tags=["session"])


@router.post("/session/end", response_model=SessionResponse)
def encerrar_sessao(requisicao: EncerrarSessaoRequest) -> SessionResponse:
    """Encerramento explícito — chamado pelo botão "nova sessão" e por
    sendBeacon quando a aba fecha. É o caminho feliz; quem não passar por
    aqui ainda é coberto pela detecção de inatividade em app/routes/chat.py.

    Sem user_id de propósito: sendBeacon não consegue mandar o header
    Authorization, então esta rota não tem como saber quem é o usuário. O
    resumo gerado aqui fica sem user_id (ver comentário em
    gerar_resumo_sessao) — não trava a rota, só não entra nas buscas de
    buscar_historico, que são sempre filtradas por user_id.
    """
    resumo = gerar_resumo_sessao(requisicao.session_id, motivo="explicita")
    return SessionResponse(session_id=requisicao.session_id, resumo=resumo)
