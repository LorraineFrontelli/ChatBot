"""
=================
Modelagem
---------
Um documento por acesso (sessão = uma conversa completa).
O _id é um UUID gerado internamente — a main.py só conhece o session_id.
O session_id identifica o usuário.

Documento
---------
{
  "_id":           "uuid-gerado-internamente",
  "session_id":    "id_usuario",
  "iniciada_em":   datetime,
  "atualizada_em": datetime,
  "resumo":        "Usuário registrou Pix de R$50...",
  "mensagens":     [
    {"role": "usuario",     "content": "oi"},
    {"role": "assistente", "content": "Olá!"}
  ]
}

Funções
----------------
  iniciar_sessao(session_id)                 → cria documento no MongoDB
  salvar_mensagem(session_id, role, content) → adiciona mensagem na sessão ativa
  encerrar_sessao(session_id)                → gera resumo e salva no documento
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from langchain_groq import ChatGroq
try:
    from pymongo import MongoClient
    from pymongo.collection import Collection
except ImportError:
    MongoClient = None
    Collection = None

load_dotenv()


# ==============================================================================
# CONEXÃO
# ==============================================================================

logger = logging.getLogger(__name__)

_mongo = None
col_sessoes = None


def _get_collection() -> Optional["Collection"]:
    global _mongo, col_sessoes

    if MongoClient is None:
        logger.warning("pymongo nao esta instalado; memoria MongoDB desativada.")
        return None

    if col_sessoes is not None:
        return col_sessoes

    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        logger.warning("MONGODB_URI nao configurada; memoria MongoDB desativada.")
        return None

    try:
        _mongo = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=1000,
        )
        _mongo.admin.command("ping")
        db = _mongo["assessor"]
        col_sessoes = db["sessoes"]
        col_sessoes.create_index("session_id")
        col_sessoes.create_index("iniciada_em")
        return col_sessoes
    except Exception:
        logger.exception("Memoria MongoDB indisponivel; seguindo sem persistencia.")
        _mongo = None
        col_sessoes = None
        return None

# ==============================================================================
# LLM PARA RESUMO
# ==============================================================================
_llm_resumo = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.0,
    api_key=os.getenv("GROQ_API_KEY"),
)

_PROMPT_RESUMO = """\
Você é um assistente que resume conversas de assessoria financeira e agenda.
Gere um resumo conciso em 2-4 frases capturando:
- O que o usuário fez (transações registradas, eventos agendados)
- O que o usuário perguntou
- Informações relevantes mencionadas (valores, datas, categorias)

Responda APENAS com o resumo, sem introdução ou explicação.

Conversa:
{conversa}
"""
_sessoes_ativas: dict = {}

def _agora() -> datetime:
    return datetime.now(timezone.utc)

def _formatar_conversa(mensagens: list[dict]) -> str:
    """Formata o array de mensagens em texto para o prompt de resumo."""
    linhas = []
    for msg in mensagens:
        linhas.append(f"{msg['role']}: {msg['content']}")
    return "\n".join(linhas)


def _gerar_resumo(mensagens: list[dict]) -> str:
    """Chama o LLM para gerar o resumo da sessão."""
    conversa = _formatar_conversa(mensagens)
    return _llm_resumo.invoke(
        _PROMPT_RESUMO.format(conversa=conversa)
    ).content.strip()


# ==============================================================================
# FUNÇÕES
# ==============================================================================
def iniciar_sessao(session_id: str) -> None: # se o session_id for int tem que mudar aqui
    """
    Cria um novo documento de sessão no MongoDB.
    O doc_id (UUID) é gerado aqui e guardado em _sessoes_ativas.
    """
    colecao = _get_collection()
    if colecao is None:
        return

    doc_id = str(uuid.uuid4())
    agora  = _agora()

    colecao.insert_one({
        "_id":           doc_id,
        "session_id":    session_id,
        "iniciada_em":   agora,
        "atualizada_em": agora,
        "resumo":        "",
        "mensagens":     [],
    })

    _sessoes_ativas[session_id] = doc_id


def salvar_mensagem(session_id: str, role: str, content: str) -> None:
    """ Adiciona uma mensagem ao array de mensagens da sessão ativa. """
    colecao = _get_collection()
    doc_id = _sessoes_ativas.get(session_id)

    if colecao is None or not doc_id:
        return

    colecao.update_one(
        {"_id": doc_id},
        {
            "$push": {"mensagens": {"role": role, "content": content}},
            "$set":  {"atualizada_em": _agora()},
        },
    )


def buscar_ultimas_mensagens(session_id: str, limite: int = 8) -> list[dict]:
    colecao = _get_collection()
    doc_id = _sessoes_ativas.get(session_id)

    if colecao is None or not doc_id:
        return []

    doc = colecao.find_one({"_id": doc_id}, {"mensagens": {"$slice": -limite}})
    return doc.get("mensagens", []) if doc else []


def buscar_ultimo_resumo(session_id: str) -> str:
    colecao = _get_collection()
    if colecao is None:
        return ""

    doc = colecao.find_one(
        {"session_id": session_id, "resumo": {"$ne": ""}},
        sort=[("atualizada_em", -1)],
    )
    return doc.get("resumo", "") if doc else ""


def encerrar_sessao(session_id) -> str:
    """
    Encerra a sessão ativa:
      1. Carrega mensagens do MongoDB
      2. Gera resumo via LLM
      3. Atualiza documento com resumo e atualizada_em
      4. Remove sessão do estado interno
    Retorna o resumo gerado ou string vazia se não houver mensagens.
    """
    colecao = _get_collection()
    doc_id = _sessoes_ativas.get(session_id)

    if colecao is None or not doc_id:
        return ""

    doc = colecao.find_one({"_id": doc_id})

    if not doc or not doc.get("mensagens"):
        _sessoes_ativas.pop(session_id, None)
        return ""

    try:
        resumo = _gerar_resumo(doc["mensagens"])
    except Exception:
        logger.exception("Erro ao gerar resumo da sessao.")
        resumo = ""

    colecao.update_one(
        {"_id": doc_id},
        {"$set": {"resumo": resumo, "atualizada_em": _agora()}},
    )

    _sessoes_ativas.pop(session_id)

    return resumo
