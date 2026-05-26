import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from mundo_invest.infrastructure.db.models import Base

_TEST_DB_URL = "sqlite+pysqlite:///file:testdb?mode=memory&cache=shared&uri=true"
os.environ["DB_URL"] = _TEST_DB_URL


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(_TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def clean_db(engine):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM processed_webhook_events"))
        conn.execute(text("DELETE FROM clientes"))
    yield


@pytest.fixture()
def app_client(session_factory, clean_db):
    from fastapi.testclient import TestClient

    from mundo_invest.interfaces.http.app import app
    from mundo_invest.interfaces.http import deps
    from mundo_invest.application.create_client import CreateClientUseCase
    from mundo_invest.application.process_card_updated import ProcessCardUpdatedUseCase
    from mundo_invest.infrastructure.db.repositories import SqlUnitOfWork
    from mundo_invest.infrastructure.pipefy.client import PipefyClient

    pipefy = PipefyClient()

    def override_create():
        return CreateClientUseCase(uow=SqlUnitOfWork(session_factory), pipefy=pipefy)

    def override_process():
        return ProcessCardUpdatedUseCase(uow=SqlUnitOfWork(session_factory), pipefy=pipefy)

    app.dependency_overrides[deps.get_create_client_use_case] = override_create
    app.dependency_overrides[deps.get_process_card_updated_use_case] = override_process

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
