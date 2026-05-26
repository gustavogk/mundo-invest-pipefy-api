import logging
from uuid import uuid4

from mundo_invest.domain.entities import Cliente
from mundo_invest.infrastructure.config import get_settings

from .mutations import CREATE_CARD_MUTATION, UPDATE_CARD_FIELD_MUTATION

logger = logging.getLogger("mundo_invest.pipefy")


class PipefyClient:
    """Loga o payload GraphQL em vez de enviar pro Pipefy de verdade."""

    def create_card(self, cliente: Cliente) -> str:
        variables = {
            "input": {
                "pipe_id": get_settings().pipefy_pipe_id,
                "title": f"Solicitação - {cliente.nome}",
                "fields_attributes": [
                    {"field_id": "cliente_nome", "field_value": cliente.nome},
                    {"field_id": "cliente_email", "field_value": cliente.email},
                    {
                        "field_id": "tipo_solicitacao",
                        "field_value": cliente.tipo_solicitacao,
                    },
                    {
                        "field_id": "valor_patrimonio",
                        "field_value": str(cliente.valor_patrimonio),
                    },
                ],
            }
        }
        payload = {"query": CREATE_CARD_MUTATION, "variables": variables}
        logger.info("pipefy.request", extra={"payload": payload})

        return f"card_{uuid4()}"

    def update_card_field(self, card_id: str, field_id: str, new_value: str) -> None:
        variables = {
            "input": {
                "card_id": card_id,
                "field_id": field_id,
                "new_value": new_value,
            }
        }
        payload = {"query": UPDATE_CARD_FIELD_MUTATION, "variables": variables}
        logger.info("pipefy.request", extra={"payload": payload})
