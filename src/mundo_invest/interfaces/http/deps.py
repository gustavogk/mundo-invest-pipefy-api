from mundo_invest.application.create_client import CreateClientUseCase
from mundo_invest.application.process_card_updated import ProcessCardUpdatedUseCase
from mundo_invest.infrastructure.db.repositories import SqlUnitOfWork
from mundo_invest.infrastructure.db.session import SessionLocal
from mundo_invest.infrastructure.pipefy.client import PipefyClient

_pipefy = PipefyClient()


def get_uow() -> SqlUnitOfWork:
    return SqlUnitOfWork(session_factory=SessionLocal)


def get_create_client_use_case() -> CreateClientUseCase:
    return CreateClientUseCase(uow=get_uow(), pipefy=_pipefy)


def get_process_card_updated_use_case() -> ProcessCardUpdatedUseCase:
    return ProcessCardUpdatedUseCase(uow=get_uow(), pipefy=_pipefy)
