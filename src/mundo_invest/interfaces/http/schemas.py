from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from mundo_invest.domain.status import Prioridade, StatusCliente


class CriarClienteRequest(BaseModel):
    cliente_nome: str = Field(min_length=1, max_length=200)
    cliente_email: EmailStr
    tipo_solicitacao: str = Field(min_length=1, max_length=100)
    valor_patrimonio: Decimal = Field(gt=0)


class CriarClienteResponse(BaseModel):
    id: UUID
    cliente_nome: str
    cliente_email: EmailStr
    tipo_solicitacao: str
    valor_patrimonio: Decimal
    status: StatusCliente
    pipefy_card_id: str


class CardUpdatedWebhookRequest(BaseModel):
    event_id: str = Field(min_length=1)
    card_id: str = Field(min_length=1)
    cliente_email: EmailStr
    timestamp: datetime


class WebhookProcessedResponse(BaseModel):
    status: str  # "processed" | "already_processed" | "not_found"
    cliente_id: str | None = None
    prioridade: Prioridade | None = None
    event_id: str | None = None
    cliente_email: str | None = None
    detail: str | None = None
