# Deploy to Google Cloud Run

## Prerequisites

```bash
gcloud auth login
gcloud config set project eastern-map-498917-i6
gcloud config set run/region asia-south1

# Enable APIs
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

## One-command deploy (backend)

```bash
gcloud run deploy disha-backend \
  --source . \
  --file backend/Dockerfile \
  --region asia-south1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --set-env-vars "DATABASE_URL=sqlite:////tmp/disha.db,SEED_FILE=/mock-data/prospects.json"
```

Cloud Run gives you a live HTTPS URL in ~3 minutes.

## With Anthropic API (Copilot)

```bash
gcloud run deploy disha-backend \
  --source . \
  --file backend/Dockerfile \
  --region asia-south1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --set-env-vars "DATABASE_URL=sqlite:////tmp/disha.db,SEED_FILE=/mock-data/prospects.json" \
  --set-secrets "ANTHROPIC_API_KEY=anthropic-api-key:latest"
```

## CI/CD (GitHub Actions)

Set these repository secrets:
- `GCP_SA_KEY` — Service account JSON with roles: `run.developer`, `artifactregistry.writer`, `cloudbuild.builds.editor`
- `GCP_PROJECT` — `eastern-map-498917-i6`

Push to `main` triggers build + deploy automatically via `.github/workflows/ci.yml`.

## Data persistence

Cloud Run containers are stateless. For production:
- Use Cloud SQL (PostgreSQL) via `DATABASE_URL=postgresql://...`
- Set `CLOUD_SQL_CONNECTION_NAME` for Cloud SQL Auth Proxy

For the hackathon demo, SQLite in `/tmp` works fine (resets on cold start — data is re-seeded from `mock-data/prospects.json` on every startup).
