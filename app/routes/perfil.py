import logging

from fastapi import APIRouter

from app.agentes.financeiro.perfil import salvar_perfil, salvar_restricoes
from app.schemas import PerfilRequest, PerfilResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["perfil"])


@router.post("/perfil", response_model=PerfilResponse)
def salvar(requisicao: PerfilRequest) -> PerfilResponse:
    """Cadastra/atualiza o perfil financeiro do usuário. Só escrita: não
    existe GET, PATCH nem DELETE de perfil (contrato da prova) — quem quer
    ver o que está salvo, olha a resposta deste POST.

    Sem autenticação de propósito (autenticação está fora de escopo aqui):
    `user_id` vem do corpo, exatamente como a tela Perfil manda. É por isso
    que o assessor, ao consultar esse cadastro pelo chat, precisa receber o
    mesmo user_id usado aqui (ver JUSTIFICATIVA.md).

    Salva nos dois bancos na mesma requisição — nada de popular o índice
    semântico só na primeira consulta. Salvar de novo substitui o cadastro
    inteiro nos dois lugares, restrições incluídas.
    """
    salvar_perfil(
        requisicao.user_id,
        requisicao.renda_mensal,
        requisicao.gasto_fixo_mensal,
        requisicao.horizonte_meses,
        requisicao.perfil_investidor,
    )
    salvar_restricoes(requisicao.user_id, requisicao.restricoes)

    logger.info("Perfil salvo: user_id=%s", requisicao.user_id)
    return PerfilResponse(**requisicao.model_dump())
