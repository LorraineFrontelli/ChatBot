"""Juiz de fidelidade. Fala antes do guardrail de saída.
Quem decide é o JEV (TypeSafe): choice e noul, sem redação.
A frase fixa, quando entra, é deste arquivo."""

import json
import logging
import urllib.error
import urllib.request

from langsmith import traceable

from app.core.config.settings import settings

logger = logging.getLogger(__name__)

JEV_URL = "https://api.typesafe.ai/v1/systemone"
JEV_MODELO = "jev-latest"
LIMIAR = 0.70
FRASE_SEGURA = "Não tenho evidência para afirmar isso."
SEM_EVIDENCIA = "(nenhuma tool devolveu conteúdo neste turno)"

REGRAS = (
    "A pergunta do usuário também é evidência do que ele disse que fez. "
    "Somas, contagens, datas convertidas para o horário de Brasília e "
    "reformatação de valores tirados da evidência contam como apoiada. "
    "Esclarecimento, saudação, oferta de ajuda, sugestão de próximo passo "
    "e ausência de registro contam como apoiada. "
    "Opinião do usuário pode ser citada como fala dele. "
    "A moeda de cada valor é a que aparece no source_text ou na fala do usuário. "
    "Moeda trocada, valores de moedas diferentes somados num total só, "
    "opinião dita como fato do sistema, número, data, telefone ou regra "
    "que não saiam da evidência contam como sem_apoio."
)


def _texto(mensagem) -> str:
    conteudo = getattr(mensagem, "content", "")
    if isinstance(conteudo, str):
        return conteudo
    if isinstance(conteudo, list):
        pedacos = []
        for parte in conteudo:
            if isinstance(parte, str):
                pedacos.append(parte)
            elif isinstance(parte, dict):
                pedacos.append(str(parte.get("text") or ""))
        return "\n".join(p for p in pedacos if p)
    return str(conteudo or "")


def coletar_evidencia(mensagens: list) -> str:
    """Retorno das tools e argumentos de cada chamada, nas mensagens que um
    sub-agente (financeiro, agenda, faq) produziu no turno. Os nós gravam
    isto em `state["evidencia"]` para o juiz ler."""
    evidencias: list[str] = []
    for mensagem in mensagens:
        tipo = getattr(mensagem, "type", "")
        if tipo == "tool":
            texto = _texto(mensagem).strip()
            if texto:
                nome = getattr(mensagem, "name", "") or "tool"
                evidencias.append(f"[{nome}]\n{texto}")
        elif tipo == "ai":
            for chamada in getattr(mensagem, "tool_calls", None) or []:
                argumentos = json.dumps(chamada.get("args", {}), ensure_ascii=False)
                evidencias.append(f"[chamada {chamada.get('name')}]\n{argumentos}")
    return "\n\n".join(evidencias).strip()[-6000:]


def _ultima_pergunta(state: dict) -> str:
    pergunta = ""
    for mensagem in state.get("messages", []):
        if getattr(mensagem, "type", "") == "human":
            pergunta = _texto(mensagem).strip() or pergunta
    return pergunta


@traceable(name="juiz_jev", run_type="chain")
def consultar_jev(pergunta: str, resposta: str, evidencia: str) -> dict:
    """Uma chamada ao JEV. É um run próprio no LangSmith: entrada (pergunta,
    resposta, evidência) e saída (choice, probabilities, noul, decisão)."""
    if not settings.TYPESAFE_API_KEY:
        return {"decisao": "sem_chave"}
    corpo = json.dumps({
        "model": JEV_MODELO,
        "state": {
            "pergunta": pergunta,
            "resposta": resposta,
            "evidencia": evidencia,
            "regras": REGRAS,
        },
        "questions": {
            "veredito": {
                "type": "choice",
                "instructions": "Seguindo as regras, a resposta só afirma o que a evidência sustenta?",
                "criteria": {
                    "apoiada": "toda afirmação factual aparece na evidência",
                    "parcial": "parte aparece e parte não",
                    "sem_apoio": "há fato, número, regra ou opinião sem evidência",
                },
            },
            "apoiada": {
                "type": "noul",
                "instructions": (
                    "Seguindo as regras, a resposta é fiel à evidência: todo valor, moeda, "
                    "data e fato dela sai da evidência, da fala do usuário ou de contas sobre elas?"
                ),
            },
        },
    }).encode()
    pedido = urllib.request.Request(
        JEV_URL,
        data=corpo,
        headers={
            "Authorization": f"Bearer {settings.TYPESAFE_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(pedido, timeout=30) as resp:
            dados = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return {"decisao": f"erro http {exc.code}"}
    veredito = dados["answers"]["veredito"]
    choice = veredito["choice"]
    noul = float(dados["answers"]["apoiada"]["noul"])
    if choice == "apoiada" and noul >= LIMIAR:
        decisao = "aprovada"
    elif choice == "apoiada":
        decisao = "apoiada:abaixo_do_limiar"
    else:
        decisao = choice
    return {
        "decisao": decisao,
        "choice": choice,
        "probabilities": veredito.get("probabilities"),
        "confidence": veredito.get("confidence"),
        "noul": noul,
        "limiar": LIMIAR,
        "modelo": dados.get("model"),
    }


def juiz_node(state: dict) -> dict:
    """Confere `resposta_bruta` contra a evidência do turno. Sem chave, erro
    ou veredito fraco, troca pela frase fixa: o fato não sai sem conferência.
    Quando troca, escreve em `resposta_bruta`, que é o que o guardrail de
    saída lê em seguida."""
    resposta = (state.get("resposta_bruta") or "").strip()
    if not resposta:
        return {"agentes_chamados": ["juiz:sem_resposta"]}

    evidencia = state.get("evidencia") or SEM_EVIDENCIA
    try:
        veredito = consultar_jev(_ultima_pergunta(state), resposta, evidencia)
    except Exception:
        logger.exception("[juiz] erro")
        veredito = {"decisao": "erro"}

    decisao = veredito["decisao"]
    rotulo = decisao
    if "noul" in veredito:
        rotulo = f"{decisao} choice={veredito['choice']} noul={veredito['noul']:.2f}"
    print(f"[juiz] {rotulo}", flush=True)

    saida = {"agentes_chamados": [f"juiz:{decisao}"]}
    if decisao != "aprovada":
        saida["resposta_bruta"] = FRASE_SEGURA
    return saida
