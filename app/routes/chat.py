from fastapi import APIRouter

from app.memory.log.interaction_log import salvar_mensagem
from app.schemas import ChatRequest, ChatResponse
from app.workflow.graph import executar_fluxo

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def conversar(requisicao: ChatRequest) -> ChatResponse:
    """Recebe uma mensagem do usuário e retorna a resposta do assessor."""
    resultado = executar_fluxo(requisicao.pergunta, requisicao.session_id)

    salvar_mensagem(requisicao.session_id, "usuario", resultado["pergunta_anonimizada"])
    salvar_mensagem(
        requisicao.session_id, "assistente", resultado["resposta"], resultado["agentes_chamados"]
    )

    return ChatResponse(
        resposta=resultado["resposta"],
        agentes_chamados=resultado["agentes_chamados"],
    )
