from fastapi import APIRouter, Depends, HTTPException, status

from mundo_invest.application.create_client import (
    CreateClientInput,
    CreateClientUseCase,
)
from mundo_invest.domain.exceptions import ClienteJaExiste
from mundo_invest.interfaces.http.deps import get_create_client_use_case
from mundo_invest.interfaces.http.schemas import (
    CriarClienteRequest,
    CriarClienteResponse,
)

router = APIRouter()


@router.post(
    "/clientes",
    response_model=CriarClienteResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_cliente(
    body: CriarClienteRequest,
    use_case: CreateClientUseCase = Depends(get_create_client_use_case),
) -> CriarClienteResponse:
    try:
        output = use_case.execute(
            CreateClientInput(
                cliente_nome=body.cliente_nome,
                cliente_email=body.cliente_email,
                tipo_solicitacao=body.tipo_solicitacao,
                valor_patrimonio=body.valor_patrimonio,
            )
        )
    except ClienteJaExiste as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cliente com email '{exc.args[0]}' já existe",
        )

    cliente = output.cliente
    return CriarClienteResponse(
        id=cliente.id,
        cliente_nome=cliente.nome,
        cliente_email=cliente.email,
        tipo_solicitacao=cliente.tipo_solicitacao,
        valor_patrimonio=cliente.valor_patrimonio,
        status=cliente.status,
        pipefy_card_id=cliente.pipefy_card_id or "",
    )
