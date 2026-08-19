import operator
from typing import Annotated

from langgraph.graph import MessagesState


class Estado(MessagesState):
    rota: str
    agentes_chamados: Annotated[list[str], operator.add]
    mapa_pii: dict
    pergunta_anonimizada: str
    resposta_roteador: str
    resposta_bruta: str
