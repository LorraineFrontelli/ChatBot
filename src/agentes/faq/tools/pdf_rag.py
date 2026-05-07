import logging

from langchain.tools import tool

from src.infraestrutura.faiss_store import get_faq_db

logger = logging.getLogger(__name__)

_db = get_faq_db()


@tool
def faq_retriver(question: str) -> str:
    """Busca no FAQ oficial os trechos mais relevantes para responder a pergunta."""
    logger.info("faq_retriver tool called")
    results = _db.similarity_search(question, k=6)
    return "\n\n".join(trecho.page_content for trecho in results)