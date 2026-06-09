---
marp: true
theme: default
paginate: true
---

# Enterprise Knowledge Copilot
## Agentic RAG for Enterprise Knowledge

**Team Vipers** · NASSCOM AI-Code-Sarathi · Final Jury 2026

*Speaker notes: Open with the problem — scattered docs and duplicate tickets slow every incident response.*

---

## Problem

- Enterprise knowledge is scattered across SOPs, IT wikis, and ticket systems
- Duplicate incidents and slow onboarding inflate resolution time
- Management bridge calls lack structured, cited status updates

*Speaker notes: Tie to 45-minute average resolution time from concept note.*

---

## Solution Overview

- Hybrid RAG over SOPs, IT docs, and support tickets
- Agent routing: ReAct (factual) vs Plan–Execute (analytical)
- Guardrails: hallucination check, confidence score, escalation
- **New:** SLA proximity badges + incident bridge brief for leadership calls

*Speaker notes: Emphasize source-cited answers, not document links.*

---

## Architecture

```
User → React UI → FastAPI → Router → Agent (ReAct / Plan–Execute / Bridge Brief)
    → HybridRetriever (Vector + BM25 + RRF)
    → LLM + Guardrails → Cited Response + SLA metadata
```

*Speaker notes: Walk left-to-right; highlight trace JSON for auditability.*

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Vector store | ChromaDB | Zero-config, persistent local index |
| Retrieval | BM25 + RRF | Lexical + semantic fusion |
| API | FastAPI | Async, test-friendly, Railway-ready |
| UI | React + Vite | Netlify deploy, rich demo UX |
| Eval | RAGAS harness | 50-Q golden set, reproducible metrics |

*Speaker notes: LangChain replaced with lean FastAPI orchestration for deploy speed.*

---

## Hybrid Retrieval + Reranker

- Dense embeddings (`all-MiniLM-L6-v2`) + BM25 keyword index
- Reciprocal Rank Fusion merges ranked lists
- Optional cross-encoder rerank (enabled locally; off on Railway for latency)

*Speaker notes: Example — “Kafka consumer deploy” hits both SOP prose and deployment tickets.*

---

## Agentic Workflow

| Query type | Agent | Example |
|------------|-------|---------|
| Factual | ReAct | “How do I deploy a Kafka consumer?” |
| Analytical | Plan–Execute | “Summarize P1 deployment tickets” |
| SLA analytics | Plan–Execute + deterministic CSV aggregation | “Which P1 tickets are at risk of SLA breach?” |
| Management brief | Bridge Brief | “Generate incident bridge brief for open P1 tickets” |

*Speaker notes: Show Agent Trace panel during demo.*

---

## Guardrails

- **Hallucination check:** embedding similarity answer ↔ citations
- **Confidence score:** overlap + citation count + coverage
- **Escalation:** below 0.65 threshold → human handoff banner
- **SLA badges:** ok / at-risk / critical / breached on ticket citations

*Speaker notes: Run edge query “What is the meaning of life?” to trigger escalation.*

---

## Live Demo Plan

1. Factual Kafka SOP query → ReAct + SOP citations
2. P1 deployment summary → Plan–Execute
3. SLA at-risk query → counts + amber/red badges
4. Incident bridge brief → 7-section leadership panel + copy
5. Edge / malicious query → escalation

*Speaker notes: Reserve 18 minutes for live demo + Q&A within 30-minute slot.*

---

## Evaluation — RAGAS (50 questions)

| Metric | Target | Result (2026-06-09) |
|--------|--------|---------------------|
| Faithfulness | ≥ 0.85 | **0.87** |
| Answer relevancy | ≥ 0.85 | 0.46* |
| Context precision | ≥ 0.80 | **0.92** |
| Citation rate | high | **100%** |

\* Heuristic proxy (retrieval-heavy run); set `OPENAI_API_KEY` for full RAGAS judge scoring.

`python tests/run_ragas.py --api-url http://localhost:8000`

*Speaker notes: 50-Q golden set — 20 factual SOP, 25 analytical ticket, 5 edge.*

---

## Scalability & Security

- **Current:** single-node Docker / Railway; ~120 indexed chunks
- **Target:** 50 QPS, ACL-tagged collections, PII redaction at ingest
- **Related work:** Karpathy LLM-Wiki pattern — we chose live RAG for freshness

*Speaker notes: Data stays in org volume; prod LLM via OpenRouter/Ollama configurable.*

---

## Thank You

**Team Vipers**  
NASSCOM AI-Code-Sarathi · Final Jury 2026

Repo: [github.com/ecogetaway/stepup](https://github.com/ecogetaway/stepup)

*Speaker notes: Invite questions on SLA proximity, bridge briefs, and eval reproducibility.*
