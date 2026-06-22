# CloudSpend Analytics API — At a Glance

**A backend REST API for cloud cost analytics & FinOps optimization.**
Ingest your cloud spend, spot anomalies, watch daily trends, and track
optimization opportunities — all over a small, clean JSON API.

> This is a **demo**. The app is intentionally small so the real star —
> how it was *built* with AWS's **AI-DLC** methodology in **Kiro** — stays in focus.
> For the build story, see [`README.md`](README.md) and [`aidlc-docs/`](aidlc-docs/).

---

## The problem it solves

Cloud bills are big, noisy, and easy to overspend on. FinOps teams need to answer:

- *How much are we spending, by service, over time?*
- *Did anything spike unexpectedly?*
- *Where can we cut cost without breaking things — and did we act on it?*

CloudSpend turns raw cost entries into those answers.

## What it does

| Capability | Endpoint | What you get |
|---|---|---|
| **Ingest cost data** | `POST /cost-data` | Record spend per service with amount, timestamp, and team tags |
| **Daily trends** | `GET /cost-data/daily` | Spend aggregated per day, paginated, filterable by service |
| **Anomaly detection** | `GET /cost-data/anomalies` | Flags days where spend runs **>25% above** the 7-day rolling average |
| **Optimization tips** | `GET /optimization/recommendations` | Ranked cost-saving opportunities (by estimated monthly savings) |
| **Track actions** | `PATCH /optimization/{id}` | Mark a recommendation *implemented* or *dismissed* |
| **Remove an entry** | `DELETE /cost-data/{id}` | Delete a cost record |
| **Health / info** | `GET /health`, `GET /` | Liveness + API metadata |

Interactive docs ship out of the box: **Swagger UI at `/docs`**, ReDoc at `/redoc`.

## Who it's for

FinOps engineers, platform teams, and anyone who needs a programmatic,
auditable view of cloud spend — without standing up a heavyweight cost platform.

## Under the hood

**Python 3.11 · FastAPI · SQLModel + SQLite · Pydantic v2 · pytest + Hypothesis.**
Money is handled as `Decimal` (never float) for exact precision. Two guardrails are
enforced across the whole build: a **Security Baseline** (HTTP security headers,
server-side validation, no internal details leaked on error) and **Property-Based
Testing** (cost math verified across randomized inputs).

## Try it in 30 seconds

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python3 -m uvicorn main:app --reload
# open http://127.0.0.1:8000/docs and click through every endpoint
```
