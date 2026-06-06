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

Results are written to `backend/tests/ragas_results.json`. Fill the table below after a run:

| Metric | Target | Result |
|--------|--------|--------|
| Faithfulness | ≥ 0.85 | _run eval_ |
| Answer relevancy | ≥ 0.85 | _run eval_ |
| Context precision | ≥ 0.80 | _run eval_ |
| Citation rate | high | _run eval_ |

## Demo script (jury)

1. **Factual:** "How do I deploy a Kafka consumer?" → ReAct, SOP citations
2. **Analytical:** "Summarize all P1 deployment tickets this month" → Plan–Execute, ticket citations
3. **Edge:** "What is the meaning of life?" → low confidence / escalation

Show the **Agent Trace** panel: router → document_search / ticket_lookup → summarizer → guardrails.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Railway + Netlify setup.

Gap tracking: [docs/GAP_CLOSURE.md](docs/GAP_CLOSURE.md)
