import logging

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from app.agentes.financeiro.perfil import buscar_restricoes_relevantes

logger = logging.getLogger(__name__)


class BuscarRestricoesPerfilArgs(BaseModel):
    pergunta: str = Field(
        ..., description="A pergunta ou o tema do conselho que está sendo avaliado, em texto livre."
    )


@tool("buscar_restricoes_perfil", args_schema=BuscarRestricoesPerfilArgs)
def buscar_restricoes_perfil(pergunta: str, config: RunnableConfig) -> dict:
    """Busca, entre as restrições cadastradas pelo usuário na tela Perfil
    (frases livres como "prefiro dormir tranquilo" ou "preciso de reserva
    para o carro"), as mais relevantes para `pergunta`. A busca é semântica:
    encontra restrições relacionadas mesmo sem palavras em comum com a
    pergunta.

    Use ANTES de recomendar algo que possa esbarrar em alguma restrição do
    usuário (travar dinheiro, investir em algo arriscado, comprometer
    reserva de emergência, etc). Se vier vazio, é porque o usuário não tem
    restrição cadastrada relevante — não é erro."""
    logger.info("buscar_restricoes_perfil tool called")
    user_id = (config or {}).get("configurable", {}).get("user_id")
    if user_id is None:
        logger.error("buscar_restricoes_perfil chamada sem user_id no config")
        return {"status": "error", "message": "Não foi possível identificar o usuário."}

    restricoes = buscar_restricoes_relevantes(str(user_id), pergunta)
    if not restricoes:
        return {"status": "ok", "restricoes": [], "message": "Nenhuma restrição cadastrada relevante."}

    return {"status": "ok", "restricoes": restricoes}
