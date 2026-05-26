from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Union

from pydantic import BaseModel, EmailStr, Field

from mundo_invest.application.ports import PipefyGateway, UnitOfWork
from mundo_invest.domain.exceptions import ClienteNotFound, DuplicateEvent
from mundo_invest.domain.priority import calcular_prioridade
from mundo_invest.domain.status import StatusCliente


class ProcessCardUpdatedInput(BaseModel):
    event_id: str = Field(min_length=1)
    card_id: str = Field(min_length=1)
    cliente_email: EmailStr
    timestamp: datetime


@dataclass
class ProcessedResult:
    cliente_id: str
    prioridade: str


@dataclass
class AlreadyProcessedResult:
    event_id: str


Result = Union[ProcessedResult, AlreadyProcessedResult]


class ProcessCardUpdatedUseCase:
    def __init__(self, uow: UnitOfWork, pipefy: PipefyGateway) -> None:
        self.uow = uow
        self.pipefy = pipefy

    def execute(self, input_data: ProcessCardUpdatedInput) -> Result:
        with self.uow as uow:
            if uow.eventos.exists(input_data.event_id):
                return AlreadyProcessedResult(event_id=input_data.event_id)

            cliente = uow.clientes.find_by_email(input_data.cliente_email)
            if cliente is None:
                raise ClienteNotFound(input_data.cliente_email)

            prioridade = calcular_prioridade(cliente.valor_patrimonio)

            # pipefy atualiza um campo por vez
            self.pipefy.update_card_field(input_data.card_id, "status", "Processado")
            self.pipefy.update_card_field(
                input_data.card_id, "prioridade", prioridade.value
            )

            updated = cliente.model_copy(
                update={
                    "status": StatusCliente.PROCESSADO,
                    "prioridade": prioridade,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            uow.clientes.update(updated)

            try:
                uow.eventos.record(
                    input_data.event_id, input_data.card_id, input_data.cliente_email
                )
            except DuplicateEvent:
                # outro webhook igual chegou ao mesmo tempo e ganhou
                uow.rollback()
                return AlreadyProcessedResult(event_id=input_data.event_id)

            uow.commit()
            return ProcessedResult(
                cliente_id=str(updated.id), prioridade=prioridade.value
            )
