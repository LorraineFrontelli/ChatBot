from .agenda.agenda_app import agenda_app
from .faq.faq_app import faq_reader_app
from .financeiro.financeiro_app import financial_app
from .orquestrador.orquestrador_app import orquestrator_app
from .router.router_app import router_app

SPECIALISTS = {
    "financeiro": financial_app,
    "agenda": agenda_app,
}

CONSULTANTS = {
    "faq": faq_reader_app,
}
