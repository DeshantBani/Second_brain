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

# raw Gemini call log (see "The raw call log & demo-resilience cache" below) -
# also browsable at /admin/agent-calls as an admin user
docker compose exec postgres psql -U sb_owner -d second_brain \
  -c "SELECT agent_name, success, replayed_from_cache, duration_ms, created_at FROM agent_call_logs ORDER BY created_at DESC LIMIT 20;"

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
Celery authority-monitoring job, the raw call log + demo-resilience replay cache, the
per-user History page, AI-aligned new-matter intake with automatic citation extraction,
conversational petition drafting with live web-researched formatting, fact-grounded
proofreading, and the full web UI.

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

## The raw call log & demo-resilience cache

Every single Gemini call - all 6 agents' structured generations and every embedding -
is logged in full to the `agent_call_logs` table: exactly what was sent (model, system
instruction, input) and exactly what came back (the raw response text), plus timing
and success/failure. Browse it live at **Agent Calls** (admin) - click any row for the
full request/response. Each query's `pipeline_run_id` links its own rows together and
back to that query's entry in **Audit Log**, so a whole run can be inspected end to
end.

**Why this exists**: a free-tier key can and does hit rate limits or transient
outages, and a live demo is exactly the wrong moment to fall back to a reasoning-free
degraded response. So every successful call is also hashed (by agent + model + exact
input) and kept as a fallback: when a live call fails for *any* reason - no key,
invalid key, 429, 503, an unexpected error - `agents_sdk/client.py` and
`services/embeddings.py` look for a prior successful response to that *exact same*
call and replay it instead of giving up. This was verified live during the build: with
`GEMINI_API_KEY` deliberately set to an invalid value, a previously-run query still
returned its full, correct result (right matter ranked, right comparison, right
**amber** reliability verdict) - just flagged `replayed_from_cache: true` instead of
silently degrading. It is never a fabricated answer - always a genuine response the
model gave at some point, replayed rather than regenerated.

Practical implication for a live presentation: **run through your demo prompts once,
successfully, before presenting** (or just use `make demo`, which seeds and doesn't
touch this cache - the three prompts in `ExamplePrompts.tsx` are already warmed as of
this build). After that, those exact queries keep working even if Gemini is
unreachable when it matters. A query's own `/history` entry and the `Replayed from a
prior real response` badge on its result page make it obvious after the fact whether a
given answer was live or replayed.

One correctness note from building this: the cache key must exclude anything that's
regenerated fresh on every call for reasons unrelated to the actual question (the
reliability agent's input originally embedded `CaseLawProvider`'s `checked_at`
timestamp, which meant it could never hit its own cache - see the comment in
`agents_sdk/reliability_agent.py::_build_input`). Worth checking for the same trap if
you add a new agent call.

## History

Every user has a **History** page (`/history`) of their own past queries, most recent
first, each one reopening the exact result they saw via the same `full_result`
snapshot `GET /query/{id}` already served for page refreshes - re-running nothing.

## New matter intake & automatic citation extraction

**New matter** (`/matters/new`): paste a past matter's document text (with optional
`## PAGE N` markers) plus a title and client name. `services/matter_intake.py` then:

1. Creates the `Matter` row and grants the submitting user access to it.
2. Ingests the text as its first `Document` (same `parse_page_map` every document goes
   through).
3. Runs the same fingerprint agent every matter in the archive uses, and writes its
   `jurisdiction`/`practice_area`/`matter_type` back onto the `Matter` row - this is
   the "AI aligns it to our structure" part: the new matter lands in the exact same
   controlled vocabulary (`agents_sdk/tools.py::TAXONOMY`) the retrieval funnel's
   structured filter depends on, rather than a human guessing at values that might not
   match what the SQL filter looks for.
4. Runs a new **citation extraction agent** (`agents_sdk/citation_extraction_agent.py`)
   over the document. Purely extractive, same grounding discipline as the comparison
   agent - every citation must carry a real page/paragraph/quote, which
   `services/matter_intake.py::extract_and_link_citations` verifies against the
   document's actual `page_map` before writing anything. The agent never determines a
   citation's legal status; that always comes from `get_case_law_provider()` - a brand
   new citation not in `MockCaseLawProvider`'s fixtures honestly resolves to `doubted`
   with no treatment history (see `mock_provider.py`), never a fabricated `good_law`.
   This is what makes the Authorities tab populate automatically instead of requiring
   a hand-written `MatterAuthority` row (previously the only way one existed, in
   `db/seed/seed_data.py`).

**Add document** (a button on an existing matter's Documents tab) runs the same
fingerprint-and-citation-extraction pipeline against `POST /documents`, re-fingerprinting
the whole matter from all its documents combined and scanning just the new one for
citations.

Verified live end to end: a new matter citing an authority already in the archive
(`ONGC v. Saw Pipes Ltd, (2003) 5 SCC 705`) correctly linked to the existing row with
its real `good_law` status; a document added to an existing matter citing a citation
never seen before correctly created a new `Authority` row with status `doubted` (the
honest "we don't have treatment data on this" default) rather than inventing one.

RLS note: creating a brand-new matter is a genuine chicken-and-egg problem for its
row-level-security policy (a matter can't have an `AccessGrant` before it exists, and
can't be inserted under RLS without one already existing). `ingest_new_matter` uses its
own `OwnerSessionLocal` for exactly this reason - the same pattern `db/seed/seed_data.py`
already relies on - since creating a matter and its first grant is a privileged,
boundary-establishing operation, not an ordinary per-row read/write. Adding a document
to an *existing* matter has no such problem and uses the caller's normal RLS-scoped
session, since the matter is already accessible to that user.

**Not covered by this**: ingesting a genuinely new case-law *authority* on its own
(independent of any matter document mentioning it) - there's still no path for that,
deliberately, since it would mean either fabricating treatment data or registering a
citation with no real status behind it at all.

## Drafting & proofreading

Two standalone features (not tied to the matter archive - a lawyer inputs a fresh case
each time), reachable from **Draft** and **Proofread** in the nav.

**Draft** (`/draft/new` → `/draft/{id}`): the lawyer describes their case in free text
(the "case brief"). A conversational **drafting-intake agent**
(`agents_sdk/drafting_intake_agent.py`) then asks follow-up questions one at a time -
"what type of petition, before which forum?", "what grounds?", "what relief?" - never
asking about anything already stated, until it has enough to draft. Once ready:

1. A **template research agent** (`agents_sdk/template_research_agent.py`) searches
   the web for that petition type's conventional format and synthesizes an ordered
   section structure from whatever it actually found - grounded in real fetched pages,
   never fabricated. The search/fetch itself (`services/web_research.py`) is plain
   HTTP + HTML parsing (DuckDuckGo's HTML endpoint, `httpx` + `BeautifulSoup`) rather
   than a browser - Google blocks non-API scraping outright, and a full headless
   Chromium buys nothing extra for finding text-based legal reference pages. Verified
   live during the build: it actually finds and cites a real source (a citation-format
   guide) for a Section 34 petition.
2. A **drafting agent** (`agents_sdk/drafting_agent.py`) writes the petition against
   that structure, section by section, grounded only in the case brief and the
   gathered requirements - verified live to stay properly scoped to the actual facts
   given (parties, figures, dates) rather than generic boilerplate.

Every draft carries an explicit "AI-drafted — review before filing" banner; there is
no auto-file or auto-send anywhere.

**Proofread** (`/proofread`): paste a draft (from anywhere - a lawyer's own work, not
just this tool's output) and, optionally, the case brief it should match. The
**proofreading agent** (`agents_sdk/proofreading_agent.py`) flags three kinds of
issues - `format` (missing/misordered sections), `content` (arguments that don't hold
together), and `missing_fact` (something material in the case brief that never made it
into the draft, quoted directly from the brief as grounding - never asserted without
being able to point to it). Framed the same way as the reliability layer elsewhere in
this system: a validator rejects any summary using clearance language ("looks good,"
"ready to file") - findings are always a prompt to verify, never an approval. Verified
live: proofreading a deliberately incomplete version of a real draft correctly caught
the exact fact that had been removed, quoting it from the case brief.

The two connect: a generated draft has a **Send to proofreading** button carrying its
text and case brief across.

Both are standalone workspaces scoped by user ownership only (`drafting_sessions`,
`proofreading_reports` - not row-level-secured/matter-linked, same pattern as
`QueryLog`), with their own history views (`/draft`, and recent reports on
`/proofread`). Every agent call in both features runs through the same
`generate_structured()` used everywhere else in this system, so it's covered by the
same raw call log and demo-resilience replay cache described above for free.

## Document upload (PDF / DOCX / TXT / MD)

Every free-text intake surface in the app - new-matter/add-document text, drafting's
case brief, proofreading's case brief and draft text - has an **Upload document**
button alongside the textarea, so a lawyer can upload a file instead of pasting.
Extraction is server-side (`services/text_extraction.py`, `POST
/uploads/extract-text`): `pypdf` for PDF text layers, `python-docx` for Word, plain
decode for TXT/MD. Uploads append to whatever's already in the field (with a small
"--- Uploaded: filename ---" header) rather than overwriting it, so multiple documents
can be combined into one case brief.

Deliberately **no OCR** (per the original build plan's scope: clean digital text and
PDFs-with-a-text-layer only, OCR as a discrete future step) - a scanned/image-only PDF
returns a clear 422 error rather than silently extracting nothing, verified with a
regression test after an early version of this let exactly that slip through (a
blank-page PDF was returning a bare `"## PAGE 1"` marker as if it were real content).

For uploads feeding matter/document ingestion (which relies on real page numbers for
source-linking - see the Matters section above), PDF page breaks are preserved as the
same `## PAGE N` markers `parse_page_map` already expects, so an uploaded PDF gets
real per-page citations exactly like pasted, manually-marked text does. DOCX has no
reliably extractable page concept, so it's treated as a single page, same as any
unmarked pasted text.
