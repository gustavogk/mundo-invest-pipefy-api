from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from .status import Prioridade, StatusCliente


class Cliente(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    nome: str
    email: EmailStr
    tipo_solicitacao: str
    valor_patrimonio: Decimal
    status: StatusCliente
    prioridade: Prioridade | None
    pipefy_card_id: str | None
    created_at: datetime
    updated_at: datetime
