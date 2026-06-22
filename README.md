# kiro-ai-dlc-demo: CloudSpend Analytics API

A **Cloud Cost Analytics REST API** built end‑to‑end with **AI‑DLC (AI Development Life Cycle)** —
AWS's spec‑driven, phase‑gated methodology for building software with an AI agent — driven from
[**Kiro**](https://kiro.dev), AWS's agentic IDE.

This repository is a **demo, not a product**. Its purpose is to show — at a deliberately small scale —
what AI‑DLC looks like in practice applied to a **FinOps use case**: instead of prompting an agent to "just write the code," you move the
work through explicit, human‑approved phases (**Inception → Construction → Operations**). At every gate
the agent writes a versioned artifact (requirements, NFR design, code‑generation plan, test report),
records every interaction in an audit log, and only proceeds once you approve.

The application itself is intentionally scoped so the *process* is the star of the show. The full trail of
how this app was produced lives in [`aidlc-docs/`](aidlc-docs/), and the methodology that drove it lives
in [`.kiro/`](.kiro/).

---

## What the app does

A pure backend JSON API for cloud cost analytics and FinOps optimization. It helps organizations ingest cloud cost data, detect spending anomalies, analyze trends, and discover cost optimization opportunities. No auth, no frontend, no UI — just a handful of REST endpoints over SQLite.

| Method | Path | Description |
|---|---|---|
| `POST` | `/cost-data` | Ingest cloud cost metrics (service, amount, timestamp, tags) |
| `GET` | `/cost-data/daily` | Daily spending trends — **cursor‑based** pagination and filterable by `service` |
| `GET` | `/cost-data/anomalies` | Detect unusual spending spikes by service |
| `GET` | `/optimization/recommendations` | List cost optimization opportunities (e.g., unused resources) |
| `PATCH` | `/optimization/{id}` | Mark recommendation as implemented/dismissed |
| `DELETE` | `/cost-data/{id}` | Remove a cost entry |
| `GET` | `/health` | Liveness check |
| `GET` | `/` | API info (name, version, doc links) |

Interactive docs are served at `/docs` (Swagger UI) and `/redoc` (ReDoc).

**Tech stack:** Python 3.11 · FastAPI · SQLModel + SQLite · Pydantic v2 · pytest + Hypothesis
(property‑based tests). Two extensions are enforced as **blocking constraints** for the whole build: a **Security Baseline** (HTTP security headers, server‑side input validation, strict error handling for financial data) and **Property‑Based Testing** (cost calculations verified across random inputs).

---

## Run it locally

```bash
# 1. Create a virtual environment and install dependencies (requires Python 3.11)
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Start the API (auto‑creates cloudspend.db on first run)
.venv/bin/python3 -m uvicorn main:app --reload

# 3. Open the interactive docs
#    http://127.0.0.1:8000/docs   (Swagger UI — try every endpoint live)
#    http://127.0.0.1:8000/redoc  (ReDoc)
```

Quick smoke test once it's running:

```bash
# Ingest a cost metric
curl -X POST http://127.0.0.1:8000/cost-data \
  -H "Content-Type: application/json" \
  -d '{"service": "EC2", "amount": 150.50, "timestamp": "2026-06-19T10:00:00Z", "tags": ["production", "web"]}'

# Fetch daily spending trends
curl "http://127.0.0.1:8000/cost-data/daily?limit=10&service=EC2"

# Get optimization recommendations
curl "http://127.0.0.1:8000/optimization/recommendations"
```

### Run the tests

```bash
.venv/bin/python3 -m pytest          # all tests
.venv/bin/python3 -m pytest -v       # verbose
```

The suite has two layers: **example‑based** tests covering specific HTTP scenarios for cost data ingestion, trend queries, and optimization recommendations, and **property‑based** tests that assert cost calculation accuracy and anomaly detection invariants over randomized inputs via Hypothesis.

---

## Project layout

```
.
├── main.py                 # FastAPI app: middleware, security headers, docs, health/root + all route handlers
├── app/
│   ├── models.py           # SQLModel tables + Pydantic schemas (CostEntry, Recommendation, etc.)
│   ├── database.py         # SQLite engine + get_session dependency + table creation
│   └── seed.py             # Seeds demo cost data + recommendations into cloudspend.db
├── tests/
│   ├── test_api.py         # Example‑based tests (CRUD, validation, security headers)
│   └── test_api_pbt.py     # Property‑based tests (Hypothesis)
├── OVERVIEW.md             # Plain‑English "what the app does" one‑pager
├── requirements.txt
├── pyproject.toml
├── aidlc-docs/             # ← every artifact AI‑DLC produced for THIS app (see below)
└── .kiro/                  # ← the AI‑DLC methodology engine (see below)
```

---

## How AI‑DLC structured the work

Two top‑level folders capture the methodology. `.kiro/` holds the **rules** the agent follows on every
project; `aidlc-docs/` holds the **artifacts those rules produced** for this specific app. Both are
committed on purpose — together they are an auditable record of *how* the code came to exist.

### `.kiro/` — the methodology engine

This is the AI‑DLC workflow itself, loaded into the agent's context as steering rules:

```
.kiro/
├── steering/
│   └── aws-aidlc-rules/
│       └── core-workflow.md          # The master workflow: phases, gates, ordering rules
└── aws-aidlc-rule-details/           # Detailed rules each phase loads on demand
    ├── common/                       # Cross‑cutting rules (process overview, question format,
    │                                 #   content validation, session continuity, audit logging)
    ├── inception/                    # Workspace detection, requirements, user stories, planning
    ├── construction/                 # Functional design, NFR design, code generation, build & test
    ├── operations/                   # Operations phase (placeholder for deploy/monitor)
    └── extensions/                   # Opt‑in rule packs
        ├── security/                 #   Security Baseline (enabled for financial data)
        └── testing/                  #   Property‑Based Testing (enabled for cost accuracy)
```

`core-workflow.md` is the heart of it. It defines three phases and the gates between them:

- **🔵 Inception** — *what to build and why.* Workspace detection → requirements analysis →
  workflow planning. (User stories, application design, and units generation are **conditional** —
  AI‑DLC may skip them if the scope is straightforward.)
- **🟢 Construction** — *how to build it.* Per‑unit loop of functional design → NFR requirements →
  NFR design → infrastructure design → code generation, followed by build & test.
- **🟡 Operations** — *how to deploy and run it.* A placeholder phase in this version.

The workflow is **adaptive** (it skips stages that add no value for a given scope) and **gated** (the
agent must present each stage's output and wait for explicit approval before continuing). Every user
input and AI action is appended to an audit log — never paraphrased.

### `aidlc-docs/` — the artifacts produced for this app

Everything the workflow generates while building *this* FinOps API, organized by phase:

```
aidlc-docs/
├── aidlc-state.md                    # Live state tracker: which stages ran, were skipped, completed
├── audit.md                          # Append‑only log of every interaction (the paper trail)
├── inception/
│   ├── requirements/                 # requirements.md + verification questions
│   └── plans/                        # execution-plan.md
└── construction/
    ├── plans/                        # Per‑stage execution plans (with checkboxes)
    ├── cost-analytics-service/
    │   ├── nfr-requirements/         # NFR requirements + tech‑stack decisions
    │   ├── nfr-design/               # Logical components + NFR design patterns
    │   └── code/                     # generation-summary.md (code is at the repo root, not here)
    └── build-and-test/               # Build & test instructions + the final test summary
```

A key rule (see `aidlc-state.md`): **application code lives at the workspace root, documentation lives
only in `aidlc-docs/`.** The docs describe and trace the code; they never contain it.

The result: every line of code traces back to a requirement, every requirement to a planned stage, and
every stage to an approval recorded in the audit log — turning an ad‑hoc "chat with an AI" into a
**repeatable, auditable development loop** for FinOps systems, which is the whole point of AI‑DLC.

---

## License

Demo / example code (MIT), provided as‑is to illustrate the AWS AI‑DLC + Kiro workflow for FinOps use cases.

