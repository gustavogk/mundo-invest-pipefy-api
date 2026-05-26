from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mundo_invest.domain.entities import Cliente
from mundo_invest.domain.exceptions import DuplicateEvent
from mundo_invest.domain.status import Prioridade, StatusCliente

from .models import ClienteORM, WebhookEventORM


def _orm_to_entity(row: ClienteORM) -> Cliente:
    return Cliente(
        id=row.id,
        nome=row.nome,
        email=row.email,
        tipo_solicitacao=row.tipo_solicitacao,
        valor_patrimonio=row.valor_patrimonio,
        status=StatusCliente(row.status),
        prioridade=Prioridade(row.prioridade) if row.prioridade else None,
        pipefy_card_id=row.pipefy_card_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlClienteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, cliente: Cliente) -> None:
        self.session.add(
            ClienteORM(
                id=cliente.id,
                nome=cliente.nome,
                email=cliente.email,
                tipo_solicitacao=cliente.tipo_solicitacao,
                valor_patrimonio=cliente.valor_patrimonio,
                status=cliente.status.value,
                prioridade=cliente.prioridade.value if cliente.prioridade else None,
                pipefy_card_id=cliente.pipefy_card_id,
                created_at=cliente.created_at,
                updated_at=cliente.updated_at,
            )
        )

    def find_by_email(self, email: str) -> Cliente | None:
        row = self.session.execute(
            select(ClienteORM).where(ClienteORM.email == email)
        ).scalar_one_or_none()
        return _orm_to_entity(row) if row else None

    def email_exists(self, email: str) -> bool:
        return (
            self.session.execute(
                select(ClienteORM.id).where(ClienteORM.email == email)
            ).scalar_one_or_none()
            is not None
        )

    def update(self, cliente: Cliente) -> None:
        row = self.session.execute(
            select(ClienteORM).where(ClienteORM.id == cliente.id)
        ).scalar_one()
        row.status = cliente.status.value
        row.prioridade = cliente.prioridade.value if cliente.prioridade else None
        row.pipefy_card_id = cliente.pipefy_card_id
        row.updated_at = cliente.updated_at


class SqlWebhookEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def exists(self, event_id: str) -> bool:
        return (
            self.session.execute(
                select(WebhookEventORM.event_id).where(
                    WebhookEventORM.event_id == event_id
                )
            ).scalar_one_or_none()
            is not None
        )

    def record(self, event_id: str, card_id: str, cliente_email: str) -> None:
        self.session.add(
            WebhookEventORM(
                event_id=event_id,
                card_id=card_id,
                cliente_email=cliente_email,
                processed_at=datetime.now(timezone.utc),
            )
        )
        try:
            self.session.flush()
        except IntegrityError as exc:
            raise DuplicateEvent(event_id) from exc


class SqlUnitOfWork:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory
        self.session: Session | None = None
        self.clientes: SqlClienteRepository | None = None
        self.eventos: SqlWebhookEventRepository | None = None

    def __enter__(self) -> "SqlUnitOfWork":
        self.session = self.session_factory()
        self.clientes = SqlClienteRepository(self.session)
        self.eventos = SqlWebhookEventRepository(self.session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self.session.rollback()
        self.session.close()
        self.session = None
        self.clientes = None
        self.eventos = None

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
