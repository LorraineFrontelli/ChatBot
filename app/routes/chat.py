from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from app.core.config.settings import settings
from app.memory.log.interaction_log import salvar_mensagem, timestamp_ultima_mensagem
from app.memory.log.session_summary import gerar_resumo_sessao
from app.schemas import ChatRequest, ChatResponse
from app.security import get_current_user_id
from app.workflow.graph import executar_fluxo

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def conversar(
    requisicao: ChatRequest, user_id: int = Depends(get_current_user_id)
) -> ChatResponse:
    """Recebe uma mensagem do usuário e retorna a resposta do assessor.

    `user_id` nunca vem do corpo da requisição — só do token (ver
    get_current_user_id), pra ninguém conseguir falar em nome de outro user
    só trocando um campo do JSON."""
    _fechar_sessao_se_ociosa(requisicao.session_id, user_id)

    resultado = executar_fluxo(requisicao.pergunta, requisicao.session_id, user_id)

    salvar_mensagem(requisicao.session_id, user_id, "usuario", resultado["pergunta_anonimizada"])
    salvar_mensagem(
        requisicao.session_id, user_id, "assistente", resultado["resposta"], resultado["agentes_chamados"]
    )

    return ChatResponse(
        resposta=resultado["resposta"],
        agentes_chamados=resultado["agentes_chamados"],
    )


def _fechar_sessao_se_ociosa(session_id: str, user_id: int) -> None:
    """Se a última mensagem desta sessão foi há mais que SESSION_IDLE_MINUTES,
    trata o que veio antes como um bloco encerrado e gera o resumo dele antes
    de processar a mensagem nova. Cobre quem nunca chama POST /session/end —
    aba fechada, bateria acabou, usuário só sumiu."""
    ultima = timestamp_ultima_mensagem(session_id)
    if ultima is None:
        return
    if datetime.now(timezone.utc) - ultima > timedelta(minutes=settings.SESSION_IDLE_MINUTES):
        gerar_resumo_sessao(session_id, motivo="inatividade", user_id=user_id)
