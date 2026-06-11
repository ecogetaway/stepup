# Enterprise Knowledge Copilot

Source-cited enterprise Q&A with hybrid RAG, agentic routing (ReAct / Plan–Execute), guardrails, and a React demo UI.

**Repository:** [https://github.com/ecogetaway/stepup](https://github.com/ecogetaway/stepup)

## Architecture

| Layer | Implementation |
|-------|----------------|
| Data | PDF SOPs, IT markdown, ticket CSV → ChromaDB + BM25 index |
| Retrieval | Dense vectors + BM25 + RRF; optional cross-encoder rerank |
| Agents | `DocumentSearchTool`, `TicketLookupTool`, `SummarizerTool` |
| Guardrails | Hallucination check, confidence score, escalation at 0.65 |
| UI | React + Vite + Tailwind (`frontend/`) |
| API | FastAPI (`backend/app/main.py`) |

### Concept note alignment

| Concept note claim | Implementation |
|--------------------|----------------|
| LangChain | FastAPI + custom agents (equivalent orchestration, leaner Railway deploy) |
| LangSmith | Runtime agent trace JSON + RAGAS eval harness; LangSmith planned for production |
| SLA proximity | Deterministic SLA compute + UI badges on ticket citations |
| Bridge brief | Structured 7-section incident brief for management calls |
| GPT-4o-mini | `LLM_PROVIDER=openai` or OpenRouter in production; Ollama for local/air-gapped |
| Streamlit | Upgraded to React production UI on Netlify |
| Multi-source RAG | SOPs, IT docs, and tickets indexed in ChromaDB |
| TicketLookupTool | `TicketLookupTool` in `backend/agents/tools.py` |

## Quick start (local)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Docker Compose:

```bash
docker compose up --build
```

Full ingestion (SOPs + IT docs + tickets):

```bash
cd backend
python scripts/reingest_all.py
```

## Evaluation

Golden set: `backend/tests/golden_qa.json` (50 questions).

| Metric | Target | How to measure |
|--------|--------|----------------|
| Faithfulness | ≥ 0.85 | RAGAS `faithfulness` |
| Answer relevancy | ≥ 0.85 | RAGAS `answer_relevancy` |
| Context precision | ≥ 0.80 | RAGAS `context_precision` |
| Citation rate | 100% on in-scope queries | Baseline metric in eval script |

Run evaluation (backend must be running):

```bash
cd backend
python tests/run_ragas.py --api-url http://localhost:8000
```

Set `OPENAI_API_KEY` for full RAGAS judge scoring; without it the script falls back to heuristic proxy metrics.

Results are written to `backend/tests/ragas_results.json`.

| Metric | Target | Result (2026-06-09, 50-Q full run) |
|--------|--------|-------------------------------------|
| Faithfulness | ≥ 0.85 | **0.87** (heuristic proxy) |
| Answer relevancy | ≥ 0.85 | 0.46 (heuristic proxy; retrieval-heavy run) |
| Context precision | ≥ 0.80 | **0.92** (heuristic proxy) |
| Citation rate | high | **100%** (50/50) |
| Avg confidence | — | 0.87 |
| Escalation rate | — | 0% |

API URL used: `http://localhost:8000` · Run `python tests/run_ragas.py --skip-ragas` for baseline-only smoke tests.

## Demo script 

1. **Factual:** "How do I deploy a Kafka consumer?" → ReAct, SOP citations
2. **Analytical:** "Summarize all P1 deployment tickets this month" → Plan–Execute, ticket citations
3. **SLA:** "Which P1 tickets are at risk of SLA breach?" → deterministic SLA counts + badges on citations
4. **Bridge brief:** "Generate incident bridge brief for open P1 tickets" → 7-section panel + copy for management
5. **Edge:** "What is the meaning of life?" → low confidence / escalation

Show the **Agent Trace** panel: router → document_search / ticket_lookup → summarizer → guardrails.

Jury deck: Presentation deck: [`decks/final-deck.md`](decks/final-deck.md)

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Railway + Netlify setup.

Gap tracking: [docs/GAP_CLOSURE.md](docs/GAP_CLOSURE.md)
