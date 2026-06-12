# Enterprise Knowledge Copilot — Design Document

**Team:** Vipers  
**Version:** 1.0 (Jury submission)  
**Last updated:** June 2026

## 1. Purpose

Enterprise Knowledge Copilot is an agentic RAG system that answers questions from enterprise SOPs, IT documentation, and support tickets with **source citations**, **confidence scoring**, and **human escalation** when answers are unreliable.

Tier 1 jury features add **SLA proximity** for operational ticket intelligence and **incident bridge briefs** for management calls.

## 2. High-Level Architecture

```
User (Browser)
    │
    ▼
React UI (Netlify) ──HTTPS──▶ FastAPI (Railway)
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              Query Router    Bridge Brief      Guardrails
                    │          Detector              │
        ┌───────────┴───────────┐                   │
        ▼                       ▼                   │
   ReAct Agent          Plan–Execute Agent          │
        │                       │                   │
        └───────────┬───────────┘                   │
                    ▼                               │
            Hybrid Retriever                        │
         (ChromaDB + BM25 + RRF)                    │
                    │                               │
                    ▼                               │
              LLM Provider                          │
         (OpenRouter / Ollama)                      │
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
                          QueryResponse JSON
                    (answer, citations, trace, SLA, brief)
```

## 3. Data Flow

| Stage | Input | Output | Failure mode |
|-------|-------|--------|--------------|
| Ingestion | PDFs, markdown, CSV | Chroma chunks + BM25 index | Empty collection → auto-ingest on startup |
| Query | Natural language question | Routed agent type | 503 if backend bootstrapping |
| Retrieval | Query string | Top-K `DocumentChunk` list | Empty → “no context” + escalation |
| Generation | Chunks + query | LLM answer with `[N]` cites | LLM fail → retrieval-only fallback |
| SLA analytics | SLA-related query | Deterministic CSV aggregation | No match → summarizer uses retrieval only |
| Bridge brief | Bridge keywords | 7-section structured brief | LLM fail → template from ticket chunks |
| Guardrails | Answer + citations | Confidence, escalation flag | Low confidence → escalation banner |

## 4. Module Responsibilities

| Module | Path | Responsibility |
|--------|------|----------------|
| API | `app/main.py` | HTTP endpoints, pipeline orchestration |
| Router | `agents/router.py` | Keyword-based agent + bridge brief detection |
| ReAct | `agents/react_agent.py` | Factual document Q&A |
| Plan–Execute | `agents/plan_execute_agent.py` | Multi-step ticket/document analysis |
| Bridge Brief | `agents/bridge_brief.py` | Management call structured output |
| SLA | `services/sla.py`, `agents/sla_analytics.py` | SLA compute + deterministic analytics |
| Tools | `agents/tools.py` | DocumentSearch, TicketLookup, Summarizer |
| Retrieval | `retrieval/hybrid_retriever.py` | Vector + BM25 + RRF |
| Guardrails | `guardrails/` | Hallucination, confidence, escalation |
| Eval | `tests/run_ragas.py` | 50-Q golden set benchmark |

## 5. Retrieval Strategy

1. **Embed query** with `all-MiniLM-L6-v2`
2. **Vector search** top-N from ChromaDB
3. **BM25 search** top-N from in-memory index
4. **RRF merge** both ranked lists (k=60)
5. **Optional rerank** with cross-encoder (local env only)
6. Return top-K chunks with metadata (`doc_type`, `priority`, `sla_*`)

## 6. Agent Design

### ReAct
- Single-pass: retrieve documents → summarize with citations
- Best for: SOP procedures, policy questions, how-to

### Plan–Execute
- Decompose query into sub-queries (keyword rules)
- Run TicketLookup + DocumentSearch per sub-query
- Merge chunks → Summarizer
- If SLA query: inject deterministic `sla_analytics` context
- Best for: ticket summaries, comparisons, SLA counts

### Bridge Brief
- Triggered by bridge/management/leadership keywords
- Retrieves P1/P2 tickets + relevant SOPs
- LLM produces fixed markdown sections → parsed to `IncidentBridgeBrief`
- Best for: executive incident updates

## 7. SLA Policy

| Priority | SLA hours |
|----------|-----------|
| P1 | 4 |
| P2 | 8 |
| P3 | 24 |

**States:** `ok` · `at_risk` (≥75% elapsed) · `critical` (≥90%) · `breached` · `resolved`

Computed at query time from `created_at`, `priority`, `status` in ticket CSV.

## 8. API Contract

### `GET /health`
Returns: `status`, `ready`, `commit`, `collection_count`, `llm_provider`, `llm_ready`

### `POST /api/v1/query`
**Request:**
```json
{
  "query": "string",
  "top_k": 5,
  "force_agent": "react | plan_execute | null",
  "output_mode": "default | bridge_brief"
}
```

**Response:**
```json
{
  "answer": "string",
  "citations": [{ "source_title", "chunk_text", "overlap_score", "doc_type", "sla" }],
  "confidence": 0.0,
  "escalated": false,
  "agent_used": "react | plan_execute | bridge_brief",
  "trace": {},
  "retrieval_ms": 0,
  "sla_summary": {},
  "bridge_brief": {}
}
```

## 9. Security & Scalability Notes

**Current:** Single Railway service, CORS restricted to Netlify origin, no PII in golden set.

**Target:** Role-based collection access, PII redaction at ingest, horizontal API replicas, dedicated embedding service, 50 QPS with GPU reranker pool.

## 10. Deployment

| Env | Frontend | Backend | LLM |
|-----|----------|---------|-----|
| Local | `localhost:5173` | `localhost:8000` | Ollama |
| Production | stepupcopilot.netlify.app | stepup-production-7453.up.railway.app | OpenRouter |

See [DEPLOYMENT.md](../DEPLOYMENT.md) for env vars and volume setup.
