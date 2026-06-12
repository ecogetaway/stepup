# Gap Closure Status — Concept Note vs. Implementation

**Team:** Vipers  
**Concept note:** `Round1Submission /Concept Note Template_V2Team-Vipers.pptx`  
**Repo:** [https://github.com/ecogetaway/stepup](https://github.com/ecogetaway/stepup)

## Closed in this implementation

| Gap | Status | Evidence |
|-----|--------|----------|
| Ticket CSV not indexed | Closed | `load_tickets_csv()` + `ingest_tickets_only()` in ingestion pipeline |
| TicketLookupTool missing | Closed | `backend/agents/tools.py` |
| DocumentSearchTool / SummarizerTool | Closed | Named tools + trace labels in agents |
| Escalation threshold 0.65 | Closed | `CONFIDENCE_ESCALATION_THRESHOLD=0.65` in config |
| RAGAS / 50-question eval | Closed | `backend/tests/golden_qa.json`, `run_ragas.py`, `ragas_results.json` (50-Q full run) |
| SLA proximity | Closed | `backend/services/sla.py`, `SlaBadge.tsx`, `sla_analytics.py` |
| Incident bridge brief | Closed | `backend/agents/bridge_brief.py`, `BridgeBriefPanel.tsx` |
| OpenAI GPT-4o-mini provider | Closed | `LLM_PROVIDER=openai` in `agents/llm.py` |
| Analytical demo chips | Closed | SLA + bridge brief suggestions in `SuggestionChips.tsx` |
| Step-by-step agent trace | Closed | `TraceViewer.tsx` step list + JSON |
| Reingest script for Railway | Closed | `scripts/reingest_all.py` |
| Presentation deck | Closed | `decks/final-deck.md` |
| LangChain / LangSmith | Documented | README architecture table; custom FastAPI equivalent |
| Streamlit UI | Documented | React + Vite production UI |

## Partial / environment-dependent

| Gap | Status | Notes |
|-----|--------|-------|
| Cross-encoder reranking | Partial | `USE_CROSS_ENCODER_RERANK=false` on Railway; enabled locally via env |
| LangSmith dashboards | Partial | Replaced by trace JSON + RAGAS + optional feedback (future) |
| RAGAS judge LLM | Partial | Full judge requires `OPENAI_API_KEY`; heuristic proxy metrics documented |
| HyDE query augmentation | Deferred | Post-submission |
| PyMuPDF / unstructured PDFs | Deferred | `pypdf` sufficient for demo PDFs |
| LLM failover chain (5s) | Deferred | Retrieval-only fallback exists today |
| Confluence / SharePoint connectors | Deferred | Out of hackathon scope |

## Verification checklist

- [x] Run `python scripts/reingest_all.py` on Railway after deploy
- [x] `/health` shows increased `collection_count` including tickets
- [x] Query `"Summarize all P1 deployment tickets this month"` returns `doc_type: ticket` citations
- [x] Run `python tests/run_ragas.py --api-url <backend-url>` and update README metrics table
- [x] SLA query returns `sla_summary` and ticket citations with `sla` badges
- [x] Bridge brief query returns structured `bridge_brief` in API response
- [ ] Live demo: factual → analytical → SLA → bridge brief → edge query

## Q&A line for judges

> We implemented equivalent agent orchestration in FastAPI for a leaner Railway deploy. Runtime trace and RAGAS eval cover prototype observability; SLA proximity and incident bridge briefs address operational leadership workflows. LangSmith is on the production roadmap.
