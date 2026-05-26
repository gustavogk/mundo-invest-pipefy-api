from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from mundo_invest.application.create_client import (
    CreateClientInput,
    CreateClientUseCase,
)
from mundo_invest.domain.entities import Cliente
from mundo_invest.domain.exceptions import ClienteJaExiste
from mundo_invest.domain.status import StatusCliente


class FakeClienteRepo:
    def __init__(self) -> None:
        self.by_id: dict[UUID, Cliente] = {}
        self.by_email: dict[str, Cliente] = {}

    def add(self, cliente: Cliente) -> None:
        self.by_id[cliente.id] = cliente
        self.by_email[cliente.email] = cliente

    def find_by_email(self, email: str) -> Cliente | None:
        return self.by_email.get(email)

    def email_exists(self, email: str) -> bool:
        return email in self.by_email

    def update(self, cliente: Cliente) -> None:
        self.by_id[cliente.id] = cliente
        self.by_email[cliente.email] = cliente


class FakeEventRepo:
    def __init__(self) -> None:
        self.records: dict[str, tuple[str, str]] = {}

    def exists(self, event_id: str) -> bool:
        return event_id in self.records

    def record(self, event_id: str, card_id: str, cliente_email: str) -> None:
        self.records[event_id] = (card_id, cliente_email)


class FakeUoW:
    def __init__(self, clientes: FakeClienteRepo, eventos: FakeEventRepo) -> None:
        self.clientes = clientes
        self.eventos = eventos
        self.committed = False
        self.rolled_back = False

    def __enter__(self) -> "FakeUoW":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None and not self.committed:
            self.rolled_back = True

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class FakePipefy:
    def __init__(self) -> None:
        self.create_calls: list[Cliente] = []
        self.update_calls: list[tuple[str, str, str]] = []
        self.stub_card_id = f"card_{uuid4()}"

    def create_card(self, cliente: Cliente) -> str:
        self.create_calls.append(cliente)
        return self.stub_card_id

    def update_card_field(self, card_id: str, field_id: str, new_value: str) -> None:
        self.update_calls.append((card_id, field_id, new_value))


@pytest.fixture
def fakes():
    clientes = FakeClienteRepo()
    eventos = FakeEventRepo()
    uow = FakeUoW(clientes, eventos)
    pipefy = FakePipefy()
    return clientes, eventos, uow, pipefy


def test_create_client_persists_with_aguardando_analise(fakes):
    clientes, _, uow, pipefy = fakes
    use_case = CreateClientUseCase(uow=uow, pipefy=pipefy)

    input_data = CreateClientInput(
        cliente_nome="João Silva",
        cliente_email="joao@example.com",
        tipo_solicitacao="Atualização cadastral",
        valor_patrimonio=Decimal("250000"),
    )

    output = use_case.execute(input_data)

    assert output.cliente.status is StatusCliente.AGUARDANDO_ANALISE
    assert output.cliente.prioridade is None
    assert output.cliente.pipefy_card_id == pipefy.stub_card_id
    assert clientes.by_email["joao@example.com"].id == output.cliente.id
    assert uow.committed is True
    assert len(pipefy.create_calls) == 1


def test_create_client_raises_when_email_exists(fakes):
    clientes, _, uow, pipefy = fakes
    use_case = CreateClientUseCase(uow=uow, pipefy=pipefy)

    input_data = CreateClientInput(
        cliente_nome="João",
        cliente_email="dup@example.com",
        tipo_solicitacao="x",
        valor_patrimonio=Decimal("100"),
    )
    use_case.execute(input_data)

    with pytest.raises(ClienteJaExiste):
        use_case.execute(input_data)


def test_pipefy_called_before_persist(fakes):
    """If create_card raised, no client row would exist — proven by ordering."""
    clientes, _, uow, pipefy = fakes

    original_add = clientes.add
    add_called_at = []

    def tracking_add(c):
        add_called_at.append(len(pipefy.create_calls))
        original_add(c)

    clientes.add = tracking_add

    use_case = CreateClientUseCase(uow=uow, pipefy=pipefy)
    use_case.execute(
        CreateClientInput(
            cliente_nome="x",
            cliente_email="x@x.com",
            tipo_solicitacao="x",
            valor_patrimonio=Decimal("1"),
        )
    )

    assert add_called_at == [1], "add must be called after create_card"
