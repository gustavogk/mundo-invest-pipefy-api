from sqlalchemy import select

from mundo_invest.infrastructure.db.models import ClienteORM


def test_post_clientes_returns_201_and_persists(app_client, session_factory):
    payload = {
        "cliente_nome": "João Silva",
        "cliente_email": "joao.silva@example.com",
        "tipo_solicitacao": "Atualização cadastral",
        "valor_patrimonio": 250000,
    }

    response = app_client.post("/clientes", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["cliente_email"] == "joao.silva@example.com"
    assert body["status"] == "aguardando_analise"
    assert body["pipefy_card_id"].startswith("card_")

    with session_factory() as session:
        row = session.execute(
            select(ClienteORM).where(ClienteORM.email == "joao.silva@example.com")
        ).scalar_one()
        assert row.status == "aguardando_analise"
        assert row.prioridade is None
        assert row.valor_patrimonio == 250000
