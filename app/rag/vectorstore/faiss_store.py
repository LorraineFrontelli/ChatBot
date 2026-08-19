"""Monta e carrega o índice FAISS usado pelo agente de FAQ."""

import os
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config.settings import FAQ_PDF_PATH, settings

# O índice fica fora da árvore do projeto, no diretório do usuário. O FAISS
# (via SWIG) abre os arquivos do índice com fopen ANSI puro no Windows: se o
# caminho do projeto tiver acento ou símbolo (ex.: "Área de Trabalho",
# "2° Ano"), a escrita/leitura falha com "No such file or directory" mesmo
# a pasta existindo. O diretório do usuário não tem esse problema.
_INDEX_PATH = str(Path.home() / ".cache" / "assessor_ia" / "faiss_index" / "faq_assessor")
_embeddings = None
_index_cache = None


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001", google_api_key=settings.GEMINI_API_KEY
        )
    return _embeddings


def build_faq_index() -> FAISS:
    loader = PyPDFLoader(str(FAQ_PDF_PATH))
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)
    index = FAISS.from_documents(chunks, _get_embeddings())
    os.makedirs(os.path.dirname(_INDEX_PATH), exist_ok=True)
    index.save_local(_INDEX_PATH)
    return index


def get_faq_db() -> FAISS:
    """Carrega o índice já persistido, ou monta na primeira chamada."""
    global _index_cache
    if _index_cache is not None:
        return _index_cache
    if os.path.exists(_INDEX_PATH):
        _index_cache = FAISS.load_local(
            _INDEX_PATH, _get_embeddings(), allow_dangerous_deserialization=True
        )
    else:
        _index_cache = build_faq_index()
    return _index_cache
