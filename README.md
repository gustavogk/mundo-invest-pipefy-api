# Mundo Invest — Pipefy API

Skeleton de API que gerencia clientes e mapeia ações de ciclo de vida para o Pipefy via mutations GraphQL. A persistência é local (SQLite por padrão); as chamadas Pipefy são simuladas via log do payload exato (mesma assinatura do que iria pra `httpx.post` em produção).

## Quickstart

Requisitos: Python 3.12+, [uv](https://docs.astral.sh/uv/). Sem Docker necessário para rodar localmente.

```bash
# 1. Instale dependências
uv sync

# 2. Aplique as migrations (cria mundo_invest.db na raiz)
uv run alembic upgrade head

# 3. Rode a API
uv run uvicorn mundo_invest.interfaces.http.app:app --reload
```

A API sobe em `http://localhost:8000`. Docs OpenAPI em `http://localhost:8000/docs`.

> **Para usar Postgres em vez de SQLite**, defina a variável de ambiente antes de rodar:
>
> ```bash
> export DB_URL="postgresql+psycopg://mundo:mundo@localhost:5432/mundo_invest"
> docker-compose up -d  # sobe o Postgres
> uv run alembic upgrade head
> uv run uvicorn mundo_invest.interfaces.http.app:app --reload
> ```

## Rodar testes

Sem Docker necessário — os testes de integração usam SQLite em memória compartilhada.

```bash
# Unit (sem banco)
uv run pytest tests/unit -q

# Integration (SQLite em memória, sem Docker)
uv run pytest tests/integration -q

# Tudo
uv run pytest -q
```

## Exemplos de API (`curl`)

No **Windows (PowerShell)**, use `curl.exe` — o comando `curl` é alias de `Invoke-WebRequest` e não aceita os mesmos argumentos. **Não use `\` para quebrar linha no PowerShell** (isso é sintaxe de Bash); o `\` vira argumento extra e o curl tenta abrir URLs inválidas (`Bad hostname`). Cole cada exemplo em **uma linha** ou use o acento grave `` ` `` no fim da linha para continuar. Os exemplos abaixo usam JSON em uma linha no `-d`.

### `POST /clientes` — criar cliente

**Sucesso (201):**

```bash
# Uma linha (PowerShell, Git Bash, Linux/macOS)
curl.exe -X POST http://localhost:8000/clientes -H "Content-Type: application/json" -d '{"cliente_nome":"João Silva","cliente_email":"joao.silva@example.com","tipo_solicitacao":"Atualização cadastral","valor_patrimonio":250000}'
```

Em Linux/macOS/Git Bash você pode quebrar com `\` e usar `curl` em vez de `curl.exe`.

**Email duplicado (409):** mesma chamada acima rodada uma segunda vez.

**Payload inválido (422):**

```bash
curl.exe -X POST http://localhost:8000/clientes -H "Content-Type: application/json" -d '{"cliente_nome":"x","cliente_email":"not-an-email","tipo_solicitacao":"x","valor_patrimonio":-1}'
```

### `POST /webhooks/pipefy/card-updated` — webhook

**Sucesso (200 `processed`):**

```bash
curl.exe -X POST http://localhost:8000/webhooks/pipefy/card-updated -H "Content-Type: application/json" -d '{"event_id":"evt_123","card_id":"card_456","cliente_email":"joao.silva@example.com","timestamp":"2026-05-25T12:00:00Z"}'
```

**Duplicata (200 `already_processed`):** mesma chamada acima rodada novamente.

**Email desconhecido (404):** trocar `cliente_email` por algo que não existe.

## Arquitetura

Light Clean Architecture. Setas apontam pra dentro.

```
interfaces/http  ──►  application  ──►  domain
                          ▲
                          │
                  infrastructure
```

- **`domain/`** — entidades + regras puras (sem imports externos). `priority.py` é dependency-free.
- **`application/`** — use cases + Protocols (`ports.py`). Não importa SQLAlchemy nem FastAPI.
- **`infrastructure/`** — implementações concretas (SQLAlchemy, Pipefy client).
- **`interfaces/http/`** — FastAPI + DI wiring (`deps.py`).

## Onde estão as mutations Pipefy

Em [`src/mundo_invest/infrastructure/pipefy/mutations.py`](src/mundo_invest/infrastructure/pipefy/mutations.py) — strings copiadas literalmente da doc:

- `createCard` — https://developers.pipefy.com/reference/createcard
- `updateCardField` — https://developers.pipefy.com/reference/updatecardfield

O `PipefyClient` em [`client.py`](src/mundo_invest/infrastructure/pipefy/client.py) monta o envelope `{"query": MUTATION, "variables": {...}}` e loga via `logger.info`. Em produção, trocar `logger.info(...)` por `httpx.post(PIPEFY_URL, json=payload, headers={"Authorization": f"Bearer {token}"})` — a assinatura dos métodos não muda.

## Visão de Produção (AWS)

**API Gateway** roteia para duas **Lambdas**: `POST /clientes` invoca a Lambda de criação (síncrona, retorna 201 com o `card_id`); `POST /webhooks/pipefy/card-updated` empilha o evento numa fila **SQS** e responde 200 imediatamente para o Pipefy (não bloqueia o emissor, ganha retry/DLQ nativos). Uma Lambda consumer drena a SQS e roda a regra de prioridade.

**RDS Postgres** guarda `clientes` — modelo relacional, joins, queries ad-hoc futuras (listagens, relatórios). **DynamoDB** guarda `processed_webhook_events` — acesso é puro key-value por `event_id`, escala horizontal sem operação, e o **TTL nativo** expira eventos antigos automaticamente (não acumula linhas mortas).

**Secrets Manager** guarda o token Pipefy (rotação gerenciada, IAM por Lambda). **CloudWatch Logs** recebe os logs estruturados; **CloudWatch Alarms** dispara em 5xx > 1%, p95 latência > 1s, ou DLQ não-vazia. **X-Ray** instrumenta o trace end-to-end.

Trade-off explicitado: SQS adiciona latência (ACK pra Pipefy não significa "processado"), mas é o que torna o sistema resiliente a picos e falhas downstream. Para volumes baixos, a Lambda síncrona direta também é defensável.
