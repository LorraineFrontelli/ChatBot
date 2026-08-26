"""Resumo de sessão — gerado tanto pelo endpoint explícito quanto pela
detecção de inatividade (ver app/routes/chat.py e app/routes/session.py).

Guarda um documento por "bloco resumido" na coleção `sessoes_resumo`, não um
documento por sessão: um mesmo session_id pode voltar a ser usado depois de
um período de inatividade, e cada vez que isso acontece um novo bloco é
fechado e resumido, sem duplicar o que já foi resumido antes.
"""
import logging
from datetime import datetime, timezone

from app.agentes.llms import fast_llm
from app.core.config.settings import settings
from app.infra.database.mongodb_client import get_mongodb_client
from app.memory.log.interaction_log import recuperar_mensagens_desde

logger = logging.getLogger(__name__)

_COLLECTION = "sessoes_resumo"

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


def _collection():
    db = get_mongodb_client()[settings.MONGODB_DB]
    col = db[_COLLECTION]
    col.create_index("session_id")
    col.create_index("encerrada_em")
    return col


def buscar_ultimo_resumo(session_id: str) -> dict | None:
    return _collection().find_one({"session_id": session_id}, sort=[("encerrada_em", -1)])


def buscar_resumos(session_id: str, busca: str | None = None, limite: int = 3) -> list[dict]:
    """Resumos de blocos já encerrados deste session_id, mais recentes primeiro.

    Usada pela tool `buscar_historico` (app/memory/tools/). O filtro
    `resumo $nin ["", None]` é essencial: sem ele, um bloco em andamento
    (ainda sem resumo) poderia aparecer como se já fosse "passado".
    Se `busca` for passado, filtra por resumos que contenham o termo
    (case-insensitive) — é uma busca literal, não semântica: sinônimo do
    termo usado no resumo original não casa.
    """
    filtro: dict = {"session_id": session_id, "resumo": {"$nin": ["", None]}}
    if busca:
        filtro["resumo"]["$regex"] = busca
        filtro["resumo"]["$options"] = "i"
    docs = _collection().find(filtro).sort("encerrada_em", -1).limit(limite)
    return list(docs)


def _formatar_conversa(mensagens: list[dict]) -> str:
    return "\n".join(f"{m['role']}: {m['content']}" for m in mensagens)


def gerar_resumo_sessao(session_id: str, motivo: str) -> str | None:
    """Resume as mensagens ainda não resumidas desta sessão (desde o último
    resumo salvo, ou desde o início, se nunca resumida) e grava o resultado.
    Retorna None se não houver mensagem nova pra resumir, ou se a LLM falhar
    — nunca levanta exceção, resumo é auxiliar, não pode travar o /chat.
    """
    ultimo = buscar_ultimo_resumo(session_id)
    desde = ultimo["mensagens_ate"] if ultimo else None

    mensagens = recuperar_mensagens_desde(session_id, desde)
    if not mensagens:
        return None

    try:
        resumo = fast_llm.invoke(
            _PROMPT_RESUMO.format(conversa=_formatar_conversa(mensagens))
        ).content.strip()
    except Exception:
        logger.exception("Falha ao gerar resumo da sessão %s; seguindo sem resumo.", session_id)
        return None

    _collection().insert_one({
        "session_id": session_id,
        "resumo": resumo,
        "mensagens_desde": mensagens[0]["timestamp"],
        "mensagens_ate": mensagens[-1]["timestamp"],
        "encerrada_em": datetime.now(timezone.utc),
        "motivo": motivo,
    })
    return resumo
