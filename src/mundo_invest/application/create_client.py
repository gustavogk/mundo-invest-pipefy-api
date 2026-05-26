from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field

from mundo_invest.application.ports import PipefyGateway, UnitOfWork
from mundo_invest.domain.entities import Cliente
from mundo_invest.domain.exceptions import ClienteJaExiste
from mundo_invest.domain.status import StatusCliente


class CreateClientInput(BaseModel):
    cliente_nome: str = Field(min_length=1, max_length=200)
    cliente_email: EmailStr
    tipo_solicitacao: str = Field(min_length=1, max_length=100)
    valor_patrimonio: Decimal = Field(gt=0)


@dataclass
class CreateClientOutput:
    cliente: Cliente


class CreateClientUseCase:
    def __init__(self, uow: UnitOfWork, pipefy: PipefyGateway) -> None:
        self.uow = uow
        self.pipefy = pipefy

    def execute(self, input_data: CreateClientInput) -> CreateClientOutput:
        with self.uow as uow:
            if uow.clientes.email_exists(input_data.cliente_email):
                raise ClienteJaExiste(input_data.cliente_email)

            now = datetime.now(timezone.utc)
            cliente_pendente = Cliente(
                id=uuid4(),
                nome=input_data.cliente_nome,
                email=input_data.cliente_email,
                tipo_solicitacao=input_data.tipo_solicitacao,
                valor_patrimonio=input_data.valor_patrimonio,
                status=StatusCliente.AGUARDANDO_ANALISE,
                prioridade=None,
                pipefy_card_id=None,
                created_at=now,
                updated_at=now,
            )

            # chama o pipefy antes de salvar pra não ficar linha no banco sem card
            card_id = self.pipefy.create_card(cliente_pendente)

            cliente = cliente_pendente.model_copy(update={"pipefy_card_id": card_id})
            uow.clientes.add(cliente)
            uow.commit()

            return CreateClientOutput(cliente=cliente)
