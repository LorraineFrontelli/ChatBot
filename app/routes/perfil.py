import logging

from fastapi import APIRouter, Depends

from app.agentes.financeiro.perfil import salvar_perfil, salvar_restricoes
from app.schemas import PerfilRequest, PerfilResponse
from app.security import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["perfil"])


@router.post("/perfil", response_model=PerfilResponse)
def salvar(
    requisicao: PerfilRequest, user_id: int = Depends(get_current_user_id)
) -> PerfilResponse:
    """Cadastra/atualiza o perfil financeiro do usuário autenticado. Só
    escrita: não existe GET, PATCH nem DELETE de perfil (contrato da prova) —
    quem quer ver o que está salvo, olha a resposta deste POST.

    `user_id` nunca vem do corpo — só do token (ver get_current_user_id), o
    mesmo que o /chat usa. Assim cada usuário só grava o próprio perfil, e o
    assessor, ao consultar o cadastro pelo chat, encontra exatamente o que
    foi salvo aqui. Gravado como string, que é como as tools do especialista
    buscam.

    Salva nos dois bancos na mesma requisição — nada de popular o índice
    semântico só na primeira consulta. Salvar de novo substitui o cadastro
    inteiro nos dois lugares, restrições incluídas.
    """
    uid = str(user_id)
    salvar_perfil(
        uid,
        requisicao.renda_mensal,
        requisicao.gasto_fixo_mensal,
        requisicao.horizonte_meses,
        requisicao.perfil_investidor,
    )
    salvar_restricoes(uid, requisicao.restricoes)

    logger.info("Perfil salvo: user_id=%s", uid)
    return PerfilResponse(**requisicao.model_dump())
