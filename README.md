# Second Brain — Legal Retrieval & Reliability System

A legal-issue-fingerprint retrieval and reliability-review engine for an Indian law
firm's internal matter archive, built for the [ILTN Vibeathon](https://vibecode.law/inspiration/challenges/iltn-vibeathon).

A lawyer describes a problem in plain language. The system extracts a structured issue
fingerprint, matches it against every prior matter's fingerprint (not keyword search),
returns ranked candidates with a stated rationale, produces a structured
similarities/differences comparison and a reusability breakdown against the best
match, and — the commercially defensible part — a graded (green/amber/red)
**reliability verdict** on whether the old matter's relied-upon case law is still good
law, sourced from a swappable `CaseLawProvider`, never from the model's own memory.
Every substantive claim carries a source pointer into an actual document page and
paragraph, verified by a blocking citation-verification guardrail before it ships.

The reliability layer is designed to never issue clearance — only a prompt to verify.

## Stack

Entirely open-source and self-hosted except one call: the Gemini API (embeddings +
reasoning for the 6-agent pipeline). No Anthropic, Azure, or AWS-managed service
anywhere in the stack. (Originally scoped around the OpenAI Agents SDK; ported to a
direct Gemini integration - see "A note on the LLM provider" below.)

- **Backend:** FastAPI (Python), LangGraph for pipeline orchestration, a direct Gemini
  API integration for the 6-agent pipeline (no LangChain model wrapper - see below)
- **Database:** Postgres + pgvector, with row-level security enforcing matter-level
  access control at the database layer (not just application logic)
- **Object storage:** MinIO (S3-compatible)
- **Background jobs:** Celery + Redis (authority-status monitoring)
- **Frontend:** Next.js (App Router) + Tailwind, a paper/editorial design system
- **Auth:** self-hosted JWT, shared identically by the web app and the scaffolded
  Outlook/Word add-in routes

See [ARCHITECTURE brief in the original build plan] for the full rationale; the short
version of what's real vs. scaffolded in this pass is in "Scope" below.

## Running it

### Prerequisites

- Docker + Docker Compose (v2 CLI plugin - `docker compose`, not `docker-compose`)
- A Gemini API key - get one free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
  (see "A note on the LLM provider" below for free-tier caveats)

### First-time setup

```bash
git clone <this repo> && cd second_brain
cp .env.example .env
# edit .env and set GEMINI_API_KEY=...

make up        # start postgres, redis, minio and wait for them to be healthy
make migrate   # create the schema + enable row-level security policies
make seed      # load the synthetic demo corpus (idempotent - safe to re-run any time)
make dev       # build and start api, worker, frontend

open http://localhost:3000
```

Demo logins (created by `make seed`):

| Account | Email | Password | Notes |
|---|---|---|---|
| Meera Nair | `lawyer1@secondbrain.test` | `lawyer123` | Access to matters M-001–M-005 |
| Arjun Rao | `lawyer2@secondbrain.test` | `lawyer123` | Access to M-006 only (isolation demo) |
| Firm Admin | `admin@secondbrain.test` | `admin123` | `/audit`, `/admin/authorities` |

### Everyday commands (`make <target>`)

| Command | What it does |
|---|---|
| `make up` | Build (if needed) and start `postgres`, `redis`, `minio` in the background |
| `make migrate` | Run `db_bootstrap` inside the api container: creates tables, enum types, the `app_user` role, and RLS policies. Safe to re-run. |
| `make seed` | Wipe and reload the synthetic demo corpus (users, matters, documents, authorities, fingerprints, embeddings). Safe to re-run any time you want a clean slate without restarting containers. |
| `make dev` | Build (if needed) and start `api`, `worker`, `frontend` in the background, alongside the infra from `make up` |
| `make logs` | Tail logs from `api`, `worker`, and `frontend` together |
| `make test` | Run the backend's pytest suite inside the api container (provider fixtures, citation guardrail, orchestrator smoke tests) |
| `make reset` | **Destructive.** `docker compose down -v` (wipes all volumes/data), then `up` → `migrate` → `seed` from scratch |
| `make demo` | `reset` + `dev`, then opens `http://localhost:3000` automatically |
| `make down` | Stop and remove all containers (keeps volumes/data) |

### One-liner variants

```bash
./scripts/demo.sh     # same as `make demo`, but checks .env exists first
```

### Doing it without `make` (equivalent raw commands)

```bash
# infra
docker compose up --build -d postgres redis minio

# migration
docker compose run --rm api python -m app.db_bootstrap

# seed
docker compose run --rm api python -m db.seed.seed_data

# app services
docker compose up --build -d api worker frontend

# tests
docker compose run --rm api pytest -q

# a single test file / a keyword filter
docker compose run --rm api pytest -q app/tests/test_guardrail.py
docker compose run --rm api pytest -q -k "reliability"

# full teardown including volumes (irreversible - deletes seeded data)
docker compose down -v
```

### Running things outside Docker (faster iteration)

Backend, in a local virtualenv (still needs `postgres`/`redis`/`minio` running via
`make up`, and `DATABASE_URL`/`DATABASE_URL_OWNER`/`REDIS_URL`/`MINIO_ENDPOINT` in
`.env` pointed at `localhost` instead of the in-network hostnames):

```bash
cd api
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload          # API on :8000
pytest -q                              # test suite, no Docker needed
python -m app.scripts.try_fingerprint "your test query here"   # exercise the fingerprint+retrieval agents standalone
```

Frontend, against a running backend (either the Docker one on `:8000`, or the local
`uvicorn` above):

```bash
cd frontend
npm install
npm run dev      # :3000, hot reload
npm run build    # production build - also the fastest way to catch TypeScript errors
npm run lint
```

### Inspecting the stack while it's running

```bash
curl -s http://localhost:8000/health | python3 -m json.tool   # llm_configured, db_ok, case_law_provider

docker compose ps                       # container status
docker compose logs -f api              # single-service logs
docker compose exec postgres psql -U sb_owner -d second_brain   # direct DB access (bypasses RLS)

open http://localhost:9001              # MinIO console (sb_minio_admin / sb_minio_dev_password from .env)
```

## The demo scenario

As `lawyer1@secondbrain.test`, submit (or click the pre-filled example prompt):

> Our client wants to exit a five year manufacturing supply agreement governed by
> Indian law. The contract has a termination for convenience clause with a thirty day
> cure period. Counterparty is threatening damages. Have we advised on this before?

Expect: **M-001** (Kesar Industries) ranks first with a stated rationale; the
Comparison tab surfaces the 45-vs-30-day cure period and pre-emptive-vs-already-asserted
damages timing as material differences, each with a real page/paragraph citation you
can click into; the Reliability tab shows an **amber** verdict grounded in a genuine
negative-treatment fixture (`Continental Constructions ... AIR 1997 Del 217`,
distinguished by a later judgment) with two named points needing fresh work; "Use in
drafting" stays locked until the Review Gate is completed, which stamps the assessment
reviewed.

Then sign in as `lawyer2@secondbrain.test` and confirm **M-006** — a highly similar
matter for the same counterparty — never appears for `lawyer1`, proving the row-level
security policy holds regardless of fingerprint similarity.

## Scope (see the build plan for the full breakdown)

**Fully real:** the data model + RLS, the three-stage retrieval funnel, all 6 agents on
the real Gemini API with graceful degradation if no key is configured, the blocking
citation-verification guardrail, `MockCaseLawProvider` with a genuine negative-treatment
fixture, confidentiality tiers, the audit log, the human-verification Review Gate, the
Celery authority-monitoring job, and the full web UI.

**Deliberately scaffolded, not deep, in this pass:** Outlook/Word (`/addin/outlook`,
`/addin/word` are route stubs — no `Office.js` dialog/token-bridge flow yet),
`IndianKanoonProvider` (documented method signatures, `NotImplementedError` bodies —
swap `CASE_LAW_PROVIDER=indiankanoon` once API access exists), OCR/scanned-document
ingestion, multi-tenant billing, and the Tier-3 public-commons workflow.

## A note on the LLM provider

This was originally scoped (see the full build plan) around the OpenAI Agents SDK as
the one paid, closed dependency, with Anthropic/Claude deliberately excluded from the
running app. Mid-build, the only key on hand was a **free-tier Gemini key**, so the
6-agent pipeline was ported to call the Gemini API directly instead - the agent
schemas, the citation-verification guardrail's actual logic, and every other layer
were untouched; only `agents_sdk/client.py` and each agent's generation call changed.

Two things worth knowing if you're evaluating this key choice:
- **Free-tier Gemini keys carry very little usable quota**, verified live against this
  key during the build: Pro-tier models return `429 RESOURCE_EXHAUSTED` immediately,
  and the full `gemini-flash-latest` model is capped around ~20 requests/day - nowhere
  near enough for even one full query (a single query makes 6-9 model calls: one
  fingerprint, one retrieval rank, one comparison, one reusability, one reliability
  call per relied-upon authority). `MODEL_FAST` and `MODEL_STRONG` both default to
  `gemini-flash-lite-latest` instead, which carries meaningfully more free daily
  quota. Bump `MODEL_STRONG` to a Pro model once on a paid key for better reasoning
  quality on the comparison/reusability/reliability steps.
- **Free-tier Gemini content is used by Google to improve their products** (paid-tier
  is not). That's a real tension for a product whose pitch is attorney-client
  confidentiality - fine for this demo, which only ever touches synthetic fixture data,
  but switch to a paid key (or back to OpenAI) before pointing this at real matters.

## A note on orchestration (LangGraph)

`services/orchestrator.py` is an explicit LangGraph `StateGraph` - every step
(fingerprint → structured filter → vector rank → retrieval → comparison → reusability
→ reliability) is a graph node operating on a shared `PipelineState`, with conditional
edges for the "no confident match" and degraded-mode branches, all declared in code
(never agent-decided, per the build plan's non-negotiable constraint). This replaced a
hand-rolled sequence of `await` calls that had grown a fair amount of repeated
result-dict-building across its early-return branches - the graph shape makes that
control flow explicit and inspectable instead.

Deliberately **not** using LangChain's model wrapper (`ChatGoogleGenerativeAI`) or
LangGraph's prebuilt agent/tool-calling abstractions (`create_react_agent`, etc.) -
every node still calls the same directly-tested `agents_sdk/client.py` Gemini
integration (with its retry-on-429/503 logic, verified against this free-tier key's
real rate limits). LangGraph here is purely an orchestration/state layer, not a new
call path to the LLM - it doesn't change API call volume, which matters a lot given
how tight that free-tier quota is. One dependency-chain note: `langgraph` pulls in
`langchain-core`, which pulls in `langsmith` (LangChain's tracing client) - it only
sends data if `LANGCHAIN_TRACING_V2`/`LANGCHAIN_API_KEY` are set (they aren't here),
but it's present in the dependency tree, same category of caveat as the free-tier
Gemini note above.
