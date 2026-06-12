# Enterprise Knowledge Copilot — Design Document

**Team:** Vipers
**Version:** 2.0 (Final submission)
**Last updated:** June 2026

## 1. Purpose

Enterprise Knowledge Copilot is an agentic RAG system that answers questions from enterprise SOPs, IT documentation, and support tickets with **source citations**, **confidence scoring**, and **human escalation** when answers are unreliable.

Operational features add **SLA proximity** for ticket intelligence and **incident bridge briefs** for management calls. Trust features add a **relevance gate** and **security block** that refuse rather than hallucinate, and a **multilingual layer** that serves Hindi/Hinglish queries from the English knowledge base.

## 2. High-Level Architecture

```
User (Browser)
    │
    ▼
React UI (Netlify) ──HTTPS──▶ FastAPI (Railway)
   · source viewer                  │
   · agent trace            Language layer (Hindi detect → translate)
   · SLA badges                     │
                                    ▼
                    ┌────── Query Router ──────┐
                    │            │             │
                    ▼            ▼             ▼
              ReAct Agent  Plan–Execute   Bridge Brief
                    │            │             │
                    └────────────┼─────────────┘
                                 ▼
                         Hybrid Retriever
                      (ChromaDB + BM25 + RRF)
                                 │
                ┌── Relevance & Security Gate ──┐
                │  out-of-scope / restricted →  │
                │  refuse · escalate · no LLM   │
                └───────────────┬───────────────┘
                                ▼
                          LLM Provider
                   (OpenRouter gpt-4o-mini / Ollama)
                                │
                ┌── Guardrails (post-generation) ──┐
                │  hallucination check · confidence │
                │  score · human escalation         │
                └───────────────┬───────────────────┘
                                ▼
                       QueryResponse JSON
        (answer, citations + full_text, trace, SLA, brief,
         out_of_scope, blocked)
```

## 3. Data Flow

| Stage | Input | Output | Failure mode |
|-------|-------|--------|--------------|
| Ingestion | PDFs, markdown, CSV | Chroma chunks + BM25 index | Empty collection → auto-ingest on startup |
| Language detection | Raw query | Language tag; Hindi queries translated to English | Translation fail → proceed with original query |
| Query | Natural language question | Routed agent type | 503 if backend bootstrapping |
| Retrieval | Query string | Top-K `DocumentChunk` list | Empty → refusal + escalation |
| Relevance gate | Query + chunks | Pass, or refusal (`out_of_scope`/`blocked`) before any LLM call | Gate error → fail open, answer normally |
| Generation | Chunks + query | LLM answer with `[N]` cites | LLM fail → retrieval-only fallback |
| SLA analytics | SLA-related query | Deterministic CSV aggregation | No match → summarizer uses retrieval only |
| Bridge brief | Bridge keywords | 7-section structured brief; model judgment labeled "Recommended:" | LLM fail → template from ticket chunks |
| Guardrails | Answer + citations | Confidence, escalation flag | Low confidence → escalation banner |
| Response language | English answer | Translated back to the query language | Translation fail → English answer returned |

## 4. Module Responsibilities

| Module | Path | Responsibility |
|--------|------|----------------|
| API | `app/main.py` | HTTP endpoints, pipeline orchestration |
| Router | `agents/router.py` | Keyword-based agent + bridge brief detection |
| ReAct | `agents/react_agent.py` | Factual document Q&A |
| Plan–Execute | `agents/plan_execute_agent.py` | Multi-step ticket/document analysis |
| Bridge Brief | `agents/bridge_brief.py` | Management call structured output |
| SLA | `services/sla.py`, `agents/sla_analytics.py` | SLA compute + deterministic analytics |
| Language | `services/language.py` | Devanagari detection, translate-retrieve-respond |
| Relevance gate | `guardrails/relevance_gate.py` | Out-of-scope refusal + restricted-intent block |
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

## 6. Trust & Guardrails

### Relevance gate (pre-generation)
Max cosine similarity between the query and the top retrieved chunks is computed **before** any LLM call. Below `RELEVANCE_GATE_THRESHOLD` (default 0.30, env-tunable), the system returns an honest refusal with **zero citations**, sets `out_of_scope: true`, escalates to a human, and logs the query as a knowledge gap. The gate fails open: an internal error never blocks answering.

### Security block
Restricted intents (e.g., "hack", "exploit", credential harvesting patterns) are blocked in ~50 ms with `blocked: true`, confidence 0, and a security-routing message — no retrieval scoring, no generation.

### Post-generation checks
Hallucination check (answer-to-citation similarity), confidence scoring, and human-escalation banner on low-confidence answers. Bridge briefs label model judgment with a "Recommended:" prefix so facts and opinion are never mixed.

**Measured effect:** edge-query escalation went from 0% (pre-gate, queries answered at ~0.82 confidence with real SOP citations) to 100% on the same golden set, with in-scope citation coverage unchanged.

## 7. Multilingual Access

Translate–retrieve–respond pipeline: Devanagari detection (≥10% of letters) → query translated to English (technical terms preserved) → standard retrieval and generation → answer translated back in a Hinglish register (deploy, consumer, config etc. stay in English). The knowledge base remains English-only and authoritative; only the access layer is multilingual. The trace exposes a `multilingual` block (detected language, original query, English query) for auditability. The same pipeline extends to other languages by adding entries to `SUPPORTED_LANGUAGES`.

## 8. SLA Policy

| Priority | SLA hours |
|----------|-----------|
| P1 | 4 |
| P2 | 8 |
| P3 | 24 |

**States:** `ok` · `at_risk` (≥75% elapsed) · `critical` (≥90%) · `breached` · `resolved`

Computed deterministically at query time from `created_at`, `priority`, `status` in the ticket CSV — never asked of the model.

## 9. API Contract

### `GET /health`
Returns: `status`, `ready`, `bootstrap_running`, `commit`, `collection_count`, `llm_provider`, `llm_ready`

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
  "citations": [{ "source_title", "chunk_text", "full_text", "overlap_score", "doc_type", "sla" }],
  "confidence": 0.0,
  "escalated": false,
  "out_of_scope": false,
  "blocked": false,
  "agent_used": "react | plan_execute | bridge_brief | guardrails",
  "trace": {},
  "retrieval_ms": 0,
  "sla_summary": {},
  "bridge_brief": {}
}
```

`citations[].full_text` powers the UI source viewer (full verbatim passage on click). `trace.multilingual` is present for non-English queries.

## 10. Security & Scalability Notes

**Current:** Single Railway service, CORS restricted to the Netlify origin, restricted-intent blocking, no PII in golden set.

**Target:** Role-based collection access, PII redaction at ingest, ITSM connectors (ServiceNow, Jira, Confluence), streaming responses with live trace, horizontal API replicas, dedicated embedding service, 50 QPS with GPU reranker pool.

## 11. Deployment

| Env | Frontend | Backend | LLM |
|-----|----------|---------|-----|
| Local | `localhost:5173` | `localhost:8000` | Ollama |
| Production | stepupcopilot.netlify.app | stepup-production-7453.up.railway.app | OpenRouter · gpt-4o-mini |

See [DEPLOYMENT.md](../DEPLOYMENT.md) for env vars and volume setup.
