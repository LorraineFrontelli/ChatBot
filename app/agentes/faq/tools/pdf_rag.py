import logging

from langchain.tools import tool

from app.rag.vectorstore.faiss_store import get_faq_db

logger = logging.getLogger(__name__)


@tool("faq_retriever")
def faq_retriever(question: str) -> str:
    """Busca no FAQ oficial os trechos mais relevantes para responder a pergunta."""
    logger.info("faq_retriever tool called")
    db = get_faq_db()  # só carrega (ou monta) na primeira chamada de verdade
    results = db.similarity_search(question, k=6)
    return "\n\n".join(trecho.page_content for trecho in results)


faq_retriver = faq_retriever
