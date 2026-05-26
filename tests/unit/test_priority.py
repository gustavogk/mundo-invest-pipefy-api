from decimal import Decimal

import pytest

from mundo_invest.domain.priority import calcular_prioridade
from mundo_invest.domain.status import Prioridade


@pytest.mark.parametrize(
    "valor,esperado",
    [
        (Decimal("0"), Prioridade.NORMAL),
        (Decimal("199999.99"), Prioridade.NORMAL),
        (Decimal("200000"), Prioridade.ALTA),
        (Decimal("200000.01"), Prioridade.ALTA),
        (Decimal("1000000"), Prioridade.ALTA),
    ],
)
def test_calcular_prioridade(valor: Decimal, esperado: Prioridade) -> None:
    assert calcular_prioridade(valor) is esperado
