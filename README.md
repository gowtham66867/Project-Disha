# Project Disha — Prospect Assist AI

**IDBI Innovate 2026 | Problem Statement 2: Prospect Assist AI**

An AI-powered lead scoring and relationship manager copilot that helps IDBI Bank RMs identify, prioritise, and convert the right prospects using deterministic scoring, explainable AI, and a Claude-powered conversational copilot.

---

## Features

| Feature | Description |
|---|---|
| **Lead Scoring Engine** | Deterministic 0–100 score with 7 weighted components (credit bureau, income, digital activity, life event, recency, existing customer, enquiry penalty) |
| **SHAP-style Breakdown** | Signed contribution bars — every point explained, auditable by regulators |
| **Next Best Action** | Product × channel × timing recommendation per segment and life event |
| **RM Copilot (Disha)** | Claude-powered chat agent with tool-use — answers "Why did PR001 score 72?" in plain language |
| **Append-only Audit Log** | Two-layer immutability: ORM + real DB triggers (SQLite & PostgreSQL) |
| **Fairness Tests** | Regression guard: identical financials → identical scores regardless of name, city, employer |
| **Pluggable Data Sources** | `SyntheticFileAdapter` (demo) and `IDBISandboxAdapter` stub (real CRM/bureau APIs) |
| **Bilingual UI** | English + Hindi support |
| **Zero-infra demo** | SQLite fallback — runs with a single `pip install` |

## Quick Start

```bash
pip install -r backend/requirements.txt
DATABASE_URL=sqlite:// SEED_FILE=mock-data/prospects.json \
  uvicorn app.main:app --app-dir backend --port 8080

# Frontend
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

## Architecture

```
React + TypeScript + Tailwind  ──► FastAPI Backend
                                     │
                     ┌───────────────┼───────────────┐
                     ▼               ▼               ▼
              Lead Scorer      NBA Engine      Disha Copilot
              (deterministic)  (rule-based)    (Claude tool-use)
                     │
              Append-only Audit Log
              (ORM + DB triggers)
                     │
              SQLite / PostgreSQL
```

## Deployment

### Google Cloud Run (one command)
```bash
gcloud run deploy disha-backend \
  --source . \
  --file backend/Dockerfile \
  --region asia-south1 \
  --allow-unauthenticated \
  --port 8080
```

See `deploy/cloudrun.md` for full instructions.

## Regulatory Alignment

- **RBI ML Governance**: Deterministic scorecard, full audit trail, weights versioned
- **DPDP Act 2023**: Purpose limitation, data minimisation, no PII in logs
- **Fair Lending**: Fairness regression tests in `backend/tests/test_fairness.py`

## Tests

```bash
DATABASE_URL=sqlite:// SEED_FILE=mock-data/prospects.json pytest backend/tests/ -v
# 19 passed
```
