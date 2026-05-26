from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Numeric, String, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ClienteORM(Base):
    __tablename__ = "clientes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    tipo_solicitacao: Mapped[str] = mapped_column(String(100), nullable=False)
    valor_patrimonio: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    prioridade: Mapped[str | None] = mapped_column(String(40), nullable=True)
    pipefy_card_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )


class WebhookEventORM(Base):
    __tablename__ = "processed_webhook_events"

    event_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    card_id: Mapped[str] = mapped_column(String(100), nullable=False)
    cliente_email: Mapped[str] = mapped_column(String(320), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
