import logging

from langchain.tools import tool

from app.vectorstore import COLLECTION_FAQ, gerar_embedding, qdrant

logger = logging.getLogger(__name__)


@tool("faq_retriever")
def faq_retriever(question: str) -> str:
    """Busca no FAQ oficial os trechos mais relevantes para responder a pergunta."""
    logger.info("faq_retriever tool called")
    vetor = gerar_embedding(question)

    resultados = qdrant.query_points(
        collection_name=COLLECTION_FAQ,
        query=vetor,
        limit=6,
    )

    if not resultados.points:
        return "Nenhum trecho relevante encontrado no FAQ."

    return "\n\n".join(
        ponto.payload["page_content"] for ponto in resultados.points
    )
