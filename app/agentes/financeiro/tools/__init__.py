from .add_transaction import add_transaction
from .buscar_restricoes_perfil import buscar_restricoes_perfil
from .consultar_perfil import consultar_perfil_financeiro
from .daily_balance import daily_balance
from .query_transactions import query_transactions
from .total_balance import total_balance
from .update_transaction import update_transaction

TOOLS = [
    add_transaction,
    buscar_restricoes_perfil,
    consultar_perfil_financeiro,
    daily_balance,
    query_transactions,
    total_balance,
    update_transaction,
]
