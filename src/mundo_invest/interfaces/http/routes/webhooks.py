from fastapi import APIRouter, Depends, status

from mundo_invest.application.process_card_updated import (
    AlreadyProcessedResult,
    ProcessCardUpdatedInput,
    ProcessCardUpdatedUseCase,
    ProcessedResult,
)
from mundo_invest.domain.exceptions import ClienteNotFound
from mundo_invest.interfaces.http.deps import get_process_card_updated_use_case
from mundo_invest.interfaces.http.schemas import (
    CardUpdatedWebhookRequest,
    WebhookProcessedResponse,
)

router = APIRouter()


@router.post(
    "/webhooks/pipefy/card-updated",
    response_model=WebhookProcessedResponse,
    status_code=status.HTTP_200_OK,
)
def card_updated(
    body: CardUpdatedWebhookRequest,
    use_case: ProcessCardUpdatedUseCase = Depends(get_process_card_updated_use_case),
) -> WebhookProcessedResponse:
    try:
        result = use_case.execute(
            ProcessCardUpdatedInput(
                event_id=body.event_id,
                card_id=body.card_id,
                cliente_email=body.cliente_email,
                timestamp=body.timestamp,
            )
        )
    except ClienteNotFound:
        # retorna 200 pra pipefy nao ficar tentando de novo sem necessidade
        return WebhookProcessedResponse(
            status="not_found",
            event_id=body.event_id,
            cliente_email=str(body.cliente_email),
            detail=f"Nenhum cliente encontrado com o email '{body.cliente_email}'",
        )

    if isinstance(result, AlreadyProcessedResult):
        return WebhookProcessedResponse(
            status="already_processed", event_id=result.event_id
        )

    assert isinstance(result, ProcessedResult)
    from mundo_invest.domain.status import Prioridade
    return WebhookProcessedResponse(
        status="processed",
        cliente_id=result.cliente_id,
        prioridade=Prioridade(result.prioridade),
    )
