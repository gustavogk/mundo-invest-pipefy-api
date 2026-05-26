from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from mundo_invest.application.process_card_updated import (
    AlreadyProcessedResult,
    ProcessCardUpdatedInput,
    ProcessCardUpdatedUseCase,
    ProcessedResult,
)
from mundo_invest.domain.entities import Cliente
from mundo_invest.domain.exceptions import ClienteNotFound
from mundo_invest.domain.status import Prioridade, StatusCliente

# Reuse fakes from test_create_client_use_case via local re-import-style copies
# (keeping unit tests self-contained avoids cross-file fixture coupling).


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

    def __enter__(self) -> "FakeUoW":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        pass

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass


class FakePipefy:
    def __init__(self) -> None:
        self.update_calls: list[tuple[str, str, str]] = []

    def create_card(self, cliente):
        raise NotImplementedError

    def update_card_field(self, card_id: str, field_id: str, new_value: str) -> None:
        self.update_calls.append((card_id, field_id, new_value))


def _make_cliente(email: str, valor: Decimal) -> Cliente:
    now = datetime.now(timezone.utc)
    return Cliente(
        id=uuid4(),
        nome="Test",
        email=email,
        tipo_solicitacao="x",
        valor_patrimonio=valor,
        status=StatusCliente.AGUARDANDO_ANALISE,
        prioridade=None,
        pipefy_card_id="card_seed",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def fakes():
    clientes = FakeClienteRepo()
    eventos = FakeEventRepo()
    uow = FakeUoW(clientes, eventos)
    pipefy = FakePipefy()
    return clientes, eventos, uow, pipefy


def test_process_returns_already_processed_on_duplicate_event(fakes):
    _, eventos, uow, pipefy = fakes
    eventos.record("evt_1", "card_seed", "x@x.com")

    use_case = ProcessCardUpdatedUseCase(uow=uow, pipefy=pipefy)
    result = use_case.execute(
        ProcessCardUpdatedInput(
            event_id="evt_1",
            card_id="card_seed",
            cliente_email="x@x.com",
            timestamp=datetime.now(timezone.utc),
        )
    )

    assert isinstance(result, AlreadyProcessedResult)
    assert result.event_id == "evt_1"
    assert pipefy.update_calls == []  # gateway never called on duplicate


def test_process_raises_cliente_not_found(fakes):
    _, _, uow, pipefy = fakes
    use_case = ProcessCardUpdatedUseCase(uow=uow, pipefy=pipefy)

    with pytest.raises(ClienteNotFound):
        use_case.execute(
            ProcessCardUpdatedInput(
                event_id="evt_x",
                card_id="card_x",
                cliente_email="ghost@x.com",
                timestamp=datetime.now(timezone.utc),
            )
        )


def test_process_assigns_priority_alta_when_patrimonio_ge_200k(fakes):
    clientes, eventos, uow, pipefy = fakes
    seed = _make_cliente("a@x.com", Decimal("250000"))
    clientes.add(seed)

    use_case = ProcessCardUpdatedUseCase(uow=uow, pipefy=pipefy)
    result = use_case.execute(
        ProcessCardUpdatedInput(
            event_id="evt_a",
            card_id="card_seed",
            cliente_email="a@x.com",
            timestamp=datetime.now(timezone.utc),
        )
    )

    assert isinstance(result, ProcessedResult)
    updated = clientes.by_email["a@x.com"]
    assert updated.status is StatusCliente.PROCESSADO
    assert updated.prioridade is Prioridade.ALTA
    assert eventos.exists("evt_a") is True
    assert pipefy.update_calls == [
        ("card_seed", "status", "Processado"),
        ("card_seed", "prioridade", "prioridade_alta"),
    ]
    assert uow.committed is True


def test_process_assigns_priority_normal_when_patrimonio_below_200k(fakes):
    clientes, _, uow, pipefy = fakes
    seed = _make_cliente("b@x.com", Decimal("150000"))
    clientes.add(seed)

    use_case = ProcessCardUpdatedUseCase(uow=uow, pipefy=pipefy)
    use_case.execute(
        ProcessCardUpdatedInput(
            event_id="evt_b",
            card_id="card_seed",
            cliente_email="b@x.com",
            timestamp=datetime.now(timezone.utc),
        )
    )

    updated = clientes.by_email["b@x.com"]
    assert updated.prioridade is Prioridade.NORMAL
    assert pipefy.update_calls[-1] == ("card_seed", "prioridade", "prioridade_normal")
