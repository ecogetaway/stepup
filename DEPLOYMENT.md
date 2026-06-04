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
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://${{Ollama.RAILWAY_PRIVATE_DOMAIN}}:11434
CONFIDENCE_ESCALATION_THRESHOLD=0.60
HALLUCINATION_SIMILARITY_THRESHOLD=0.35
```

Persistence strategy:

- Mount a Railway volume at `/data` for generated PDFs, ticket CSVs, and other source documents.
- Mount a Railway volume at `/chroma_db` for the Chroma vector store.
- If your Railway plan only allows one volume, mount it at `/data` and set `CHROMA_PERSIST_DIR=/data/chroma_db`.
- For the Ollama service, mount a volume at `/root/.ollama` so the pulled model survives restarts.

Create a separate Railway Ollama service from `ollama/ollama:latest`, expose port `11434` privately, and set the backend `OLLAMA_BASE_URL` to that service's private URL. Pull the model once in the Ollama service:

```bash
ollama pull llama3.2:3b
```

After volumes are attached, run ingestion once from the backend service shell:

```bash
python scripts/generate_sample_data.py
python scripts/generate_tickets.py
python scripts/ingest.py
```

Verify:

```bash
curl https://<your-railway-backend-domain>/health
```

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
OLLAMA_BASE_URL=http://ollama:11434
CHROMA_PERSIST_DIR=/app/data/chroma_db
```

Run locally with:

```bash
docker compose up --build
```
