from decimal import Decimal

from .status import Prioridade

LIMIAR_PATRIMONIO = Decimal("200000")


def calcular_prioridade(valor_patrimonio: Decimal) -> Prioridade:
    if valor_patrimonio >= LIMIAR_PATRIMONIO:
        return Prioridade.ALTA
    return Prioridade.NORMAL
