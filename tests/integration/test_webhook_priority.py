import pytest
from sqlalchemy import select

from mundo_invest.infrastructure.db.models import ClienteORM


def _create(app_client, email: str, valor: int) -> dict:
    res = app_client.post(
        "/clientes",
        json={
            "cliente_nome": "Test",
            "cliente_email": email,
            "tipo_solicitacao": "x",
            "valor_patrimonio": valor,
        },
    )
    assert res.status_code == 201
    return res.json()


@pytest.mark.parametrize(
    "valor,prioridade_esperada",
    [(250000, "prioridade_alta"), (150000, "prioridade_normal")],
)
def test_webhook_assigns_priority_by_patrimony(
    app_client, session_factory, valor, prioridade_esperada
):
    cliente = _create(app_client, f"user_{valor}@x.com", valor)

    response = app_client.post(
        "/webhooks/pipefy/card-updated",
        json={
            "event_id": f"evt_{valor}",
            "card_id": cliente["pipefy_card_id"],
            "cliente_email": cliente["cliente_email"],
            "timestamp": "2026-05-25T12:00:00Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["prioridade"] == prioridade_esperada

    with session_factory() as session:
        row = session.execute(
            select(ClienteORM).where(ClienteORM.email == cliente["cliente_email"])
        ).scalar_one()
        assert row.status == "processado"
        assert row.prioridade == prioridade_esperada
