import pytest


# ---------------------------------------------------------------------------
# POST /clientes — validação de entrada
# ---------------------------------------------------------------------------

VALID_CLIENTE = {
    "cliente_nome": "João Silva",
    "cliente_email": "joao@example.com",
    "tipo_solicitacao": "Atualização cadastral",
    "valor_patrimonio": 100000,
}


@pytest.mark.parametrize(
    "override,expected_status",
    [
        ({"cliente_email": "not-an-email"}, 422),
        ({"cliente_email": "missing-at-sign"}, 422),
        ({"valor_patrimonio": 0}, 422),
        ({"valor_patrimonio": -1}, 422),
        ({"cliente_nome": ""}, 422),
        ({"tipo_solicitacao": ""}, 422),
    ],
)
def test_create_cliente_rejects_invalid_payload(app_client, override, expected_status):
    payload = {**VALID_CLIENTE, **override}
    response = app_client.post("/clientes", json=payload)
    assert response.status_code == expected_status


@pytest.mark.parametrize("missing_field", ["cliente_nome", "cliente_email", "tipo_solicitacao", "valor_patrimonio"])
def test_create_cliente_rejects_missing_required_field(app_client, missing_field):
    payload = {k: v for k, v in VALID_CLIENTE.items() if k != missing_field}
    response = app_client.post("/clientes", json=payload)
    assert response.status_code == 422


def test_create_cliente_rejects_duplicate_email(app_client):
    app_client.post("/clientes", json=VALID_CLIENTE)
    response = app_client.post("/clientes", json=VALID_CLIENTE)
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# POST /webhooks/pipefy/card-updated — validação de entrada
# ---------------------------------------------------------------------------

VALID_WEBHOOK = {
    "event_id": "evt_001",
    "card_id": "card_001",
    "cliente_email": "joao@example.com",
    "timestamp": "2026-05-25T12:00:00Z",
}


@pytest.mark.parametrize(
    "override,expected_status",
    [
        ({"cliente_email": "not-an-email"}, 422),
        ({"event_id": ""}, 422),
        ({"card_id": ""}, 422),
        ({"timestamp": "not-a-date"}, 422),
    ],
)
def test_webhook_rejects_invalid_payload(app_client, override, expected_status):
    payload = {**VALID_WEBHOOK, **override}
    response = app_client.post("/webhooks/pipefy/card-updated", json=payload)
    assert response.status_code == expected_status


@pytest.mark.parametrize("missing_field", ["event_id", "card_id", "cliente_email", "timestamp"])
def test_webhook_rejects_missing_required_field(app_client, missing_field):
    payload = {k: v for k, v in VALID_WEBHOOK.items() if k != missing_field}
    response = app_client.post("/webhooks/pipefy/card-updated", json=payload)
    assert response.status_code == 422


def test_webhook_returns_200_not_404_for_unknown_email(app_client):
    """Pipefy retries on non-2xx — unknown email must not trigger infinite retries."""
    response = app_client.post("/webhooks/pipefy/card-updated", json=VALID_WEBHOOK)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_found"
    assert body["cliente_email"] == VALID_WEBHOOK["cliente_email"]
    assert body["event_id"] == VALID_WEBHOOK["event_id"]
    assert VALID_WEBHOOK["cliente_email"] in body["detail"]
