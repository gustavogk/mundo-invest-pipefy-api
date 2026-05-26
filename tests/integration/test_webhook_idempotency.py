from sqlalchemy import func, select

from mundo_invest.infrastructure.db.models import ClienteORM, WebhookEventORM


def test_duplicate_event_returns_already_processed_and_no_extra_row(
    app_client, session_factory
):
    create_res = app_client.post(
        "/clientes",
        json={
            "cliente_nome": "Idem",
            "cliente_email": "idem@x.com",
            "tipo_solicitacao": "x",
            "valor_patrimonio": 300000,
        },
    )
    assert create_res.status_code == 201
    cliente = create_res.json()

    webhook_payload = {
        "event_id": "evt_dup",
        "card_id": cliente["pipefy_card_id"],
        "cliente_email": "idem@x.com",
        "timestamp": "2026-05-25T12:00:00Z",
    }

    first = app_client.post("/webhooks/pipefy/card-updated", json=webhook_payload)
    assert first.status_code == 200
    assert first.json()["status"] == "processed"

    # Capture the updated_at after first call.
    with session_factory() as session:
        row1 = session.execute(
            select(ClienteORM).where(ClienteORM.email == "idem@x.com")
        ).scalar_one()
        updated_at_after_first = row1.updated_at

    second = app_client.post("/webhooks/pipefy/card-updated", json=webhook_payload)
    assert second.status_code == 200
    body = second.json()
    assert body["status"] == "already_processed"
    assert body["event_id"] == "evt_dup"

    # Client row not touched again.
    with session_factory() as session:
        row2 = session.execute(
            select(ClienteORM).where(ClienteORM.email == "idem@x.com")
        ).scalar_one()
        assert row2.updated_at == updated_at_after_first

        # Exactly 1 event row.
        count = session.execute(
            select(func.count()).select_from(WebhookEventORM).where(
                WebhookEventORM.event_id == "evt_dup"
            )
        ).scalar_one()
        assert count == 1
