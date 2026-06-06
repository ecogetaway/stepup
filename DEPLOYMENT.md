# Deployment Guide

This app is configured for Railway backend deployment and Netlify frontend deployment while keeping local Docker Compose unchanged.

## Railway Backend

Create a Railway service for `backend/` and use `backend/railway.toml`. Railway should build from the backend Dockerfile and bind FastAPI to the platform-provided `PORT`.

Set these backend variables:

```bash
APP_ENV=production
CORS_ORIGINS=https://<your-netlify-site>.netlify.app
DATA_DIR=/data
SOP_DIR=/data/sops
IT_DOCS_DIR=/data/it_docs
TICKET_CSV=/data/tickets/tickets.csv
CHROMA_PERSIST_DIR=/chroma_db
CHROMA_COLLECTION=enterprise_docs
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANKER_TOP_K=5
BM25_TOP_K=20
VECTOR_TOP_K=20
RRF_K=60
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=<your-openrouter-api-key>
OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_HTTP_REFERER=https://<your-netlify-site>.netlify.app
CONFIDENCE_ESCALATION_THRESHOLD=0.65
HALLUCINATION_SIMILARITY_THRESHOLD=0.35
```

Production LLM recommendation:

- Use OpenRouter with NVIDIA Nemotron 3 Ultra on Railway. Ollama is kept for local Docker Compose only.
- Get an API key from https://openrouter.ai and set `OPENROUTER_API_KEY` on the backend service.
- If the hosted LLM fails, the backend falls back to citation-based answers from retrieved documents.

Persistence strategy:

- Mount a Railway volume at `/data` for generated PDFs, ticket CSVs, and other source documents.
- Mount a Railway volume at `/chroma_db` for the Chroma vector store.
- If your Railway plan only allows one volume, mount it at `/data` and set `CHROMA_PERSIST_DIR=/data/chroma_db`.
- Without volumes, keep `DATA_DIR=./data` and `CHROMA_PERSIST_DIR=./data/chroma_db`, then re-run ingest after each redeploy.

After volumes are attached, run ingestion once from the backend service shell:

```bash
python scripts/reingest_all.py
```

Or step by step:

```bash
python scripts/generate_sample_data.py
python scripts/generate_tickets.py
python scripts/ingest.py
```

If Chroma already has SOP/IT chunks but no tickets, restart the service (startup auto-ingests tickets) or run:

```bash
python -c "from ingestion.pipeline import ingest_tickets_only; ingest_tickets_only()"
```

Verify:

```bash
curl https://<your-railway-backend-domain>/health
```

Post-deploy smoke tests (replace `API` with your Railway URL):

```bash
API=https://<your-railway-backend-domain>

curl -s "$API/health" | python3 -m json.tool

curl -s -X POST "$API/api/v1/query" -H 'Content-Type: application/json' \
  -d '{"query":"How do I deploy a Kafka consumer?","top_k":3}'

curl -s -X POST "$API/api/v1/query" -H 'Content-Type: application/json' \
  -d '{"query":"Summarize all P1 deployment tickets this month","top_k":5}'

curl -s -X POST "$API/api/v1/query" -H 'Content-Type: application/json' \
  -d '{"query":"What is the meaning of life?","top_k":3}'
```

Run evaluation against production:

```bash
cd backend
python tests/run_ragas.py --api-url https://<your-railway-backend-domain>
```

Update the metrics table in [README.md](README.md) with the output.

## Netlify Frontend

The root `netlify.toml` builds the Vite app from `frontend/` and publishes `frontend/dist`.

Set this Netlify environment variable before building:

```bash
VITE_API_URL=https://<your-railway-backend-domain>
```

Deploy after the Railway backend is healthy so the build gets the final backend URL. The SPA redirect is already configured in `netlify.toml`.

## Local Docker Compose

Local Compose still uses:

```bash
VITE_API_URL=http://localhost:8000
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
CHROMA_PERSIST_DIR=/app/data/chroma_db
```

Run locally with:

```bash
docker compose up --build
```
