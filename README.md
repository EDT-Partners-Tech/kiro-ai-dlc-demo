# kiro-ai-dlc-demo

A small **Blog Posts REST API** built end‑to‑end with **AI‑DLC (AI Development Life Cycle)** —
AWS's spec‑driven, phase‑gated methodology for building software with an AI agent — driven from
[**Kiro**](https://kiro.dev), AWS's agentic IDE.

This repository is a **demo, not a product**. Its purpose is to show — at a deliberately small scale —
what AI‑DLC looks like in practice: instead of prompting an agent to "just write the code," you move the
work through explicit, human‑approved phases (**Inception → Construction → Operations**). At every gate
the agent writes a versioned artifact (requirements, NFR design, code‑generation plan, test report),
records every interaction in an audit log, and only proceeds once you approve.

The application itself is intentionally tiny so the *process* is the star of the show. The full trail of
how this app was produced lives in [`aidlc-docs/`](aidlc-docs/), and the methodology that drove it lives
in [`.kiro/`](.kiro/).

---

## What the app does

A pure backend JSON API for managing blog posts and their tags. No auth, no frontend, no UI — just a
handful of endpoints over SQLite.

| Method | Path | Description |
|---|---|---|
| `POST` | `/posts` | Create a post (`title`, `content`, optional `tags`) |
| `GET` | `/posts` | List posts — **cursor‑based** pagination (`cursor`, `limit`) and filterable by `tag` |
| `GET` | `/posts/{id}` | Fetch a single post |
| `PATCH` | `/posts/{id}` | Partial update (any subset of `title`, `content`, `tags`) |
| `DELETE` | `/posts/{id}` | Delete a post |
| `GET` | `/health` | Liveness check |
| `GET` | `/` | API info (name, version, doc links) |

Interactive docs are served at `/docs` (Swagger UI) and `/redoc` (ReDoc).

**Tech stack:** Python 3.9+ · FastAPI · SQLModel + SQLite · Pydantic v2 · pytest + Hypothesis
(property‑based tests). Two extensions were opted into during Inception and enforced as **blocking
constraints** for the whole build: a **Security Baseline** (HTTP security headers, server‑side input
validation, safe error handling) and **Property‑Based Testing**.

---

## Run it locally

```bash
# 1. Create a virtual environment and install dependencies
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Start the API (auto‑creates blog-posts.db on first run)
.venv/bin/python3 -m uvicorn main:app --reload

# 3. Open the interactive docs
#    http://127.0.0.1:8000/docs   (Swagger UI — try every endpoint live)
#    http://127.0.0.1:8000/redoc  (ReDoc)
```

Quick smoke test once it's running:

```bash
curl -X POST http://127.0.0.1:8000/posts \
  -H "Content-Type: application/json" \
  -d '{"title": "Hello AI-DLC", "content": "First post.", "tags": ["demo", "aws"]}'

curl "http://127.0.0.1:8000/posts?limit=10&tag=demo"
```

### Run the tests

```bash
.venv/bin/python3 -m pytest          # all 35 tests
.venv/bin/python3 -m pytest -v       # verbose
```

The suite has two layers: **example‑based** tests (`tests/test_api.py`, 26 tests) covering specific HTTP
scenarios, and **property‑based** tests (`tests/test_api_pbt.py`, 9 tests) that assert serialization
round‑trips and field/pagination invariants over randomized inputs via Hypothesis.

---

## Project layout

```
.
├── main.py                 # FastAPI app: middleware, docs, health/root, startup
├── app/
│   ├── models.py           # SQLModel tables + Pydantic schemas (BlogPost, Tag, pagination)
│   ├── database.py         # SQLite engine + get_session dependency + table creation
│   └── api/
│       └── endpoints.py    # The /posts CRUD + list/pagination/filter handlers
├── tests/
│   ├── test_api.py         # Example‑based tests (CRUD, validation, security headers)
│   └── test_api_pbt.py     # Property‑based tests (Hypothesis)
├── docs/                   # Human‑authored API reference (README.md, API.md)
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
        ├── security/                 #   Security Baseline (enabled here)
        └── testing/                  #   Property‑Based Testing (enabled here)
```

`core-workflow.md` is the heart of it. It defines three phases and the gates between them:

- **🔵 Inception** — *what to build and why.* Workspace detection → requirements analysis →
  workflow planning. (User stories, application design, and units generation are **conditional** —
  AI‑DLC skipped them here because the scope was a single, straightforward CRUD service.)
- **🟢 Construction** — *how to build it.* Per‑unit loop of functional design → NFR requirements →
  NFR design → infrastructure design → code generation, followed by build & test.
- **🟡 Operations** — *how to deploy and run it.* A placeholder phase in this version.

The workflow is **adaptive** (it skips stages that add no value for a small scope) and **gated** (the
agent must present each stage's output and wait for explicit approval before continuing). Every user
input and AI action is appended to an audit log — never paraphrased.

### `aidlc-docs/` — the artifacts produced for this app

Everything the workflow generated while building *this* API, organized by phase:

```
aidlc-docs/
├── aidlc-state.md                    # Live state tracker: which stages ran, were skipped, completed
├── audit.md                          # Append‑only log of every interaction (the paper trail)
├── inception/
│   ├── requirements/                 # requirements.md + verification questions
│   └── plans/                        # execution-plan.md
└── construction/
    ├── plans/                        # Per‑stage execution plans (with checkboxes)
    ├── api-service/
    │   ├── nfr-requirements/         # NFR requirements + tech‑stack decisions
    │   ├── nfr-design/               # Logical components + NFR design patterns
    │   └── code/                     # generation-summary.md (code is at the repo root, not here)
    └── build-and-test/               # Build & test instructions + the final test summary
```

A key rule (see `aidlc-state.md`): **application code lives at the workspace root, documentation lives
only in `aidlc-docs/`.** The docs describe and trace the code; they never contain it.

The result: every line of code traces back to a requirement, every requirement to a planned stage, and
every stage to an approval recorded in the audit log — turning an ad‑hoc "chat with an AI" into a
**repeatable, auditable development loop**, which is the whole point of AI‑DLC.

---

## License

Demo / example code (MIT), provided as‑is to illustrate the AWS AI‑DLC + Kiro workflow.
