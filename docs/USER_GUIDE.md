# Enterprise Knowledge Copilot — User Guide

**Live app:** https://stepupcopilot.netlify.app
**Team:** Vipers

## Who is this for?

- **L1/L2 support engineers** — find SOP steps and related tickets quickly, in English or Hindi
- **Incident commanders** — summarize P1/P2 tickets and check SLA risk
- **Managers / bridge call leads** — generate structured incident briefs
- **New hires** — onboard faster with cited answers from internal docs

## Getting started

1. Open https://stepupcopilot.netlify.app
2. Wait for the header health indicator to show the backend is connected
3. Click a suggestion chip — it submits immediately — or type your own question
4. For typed questions, press **Get Answer** or `Cmd+Enter` / `Ctrl+Enter` (works from anywhere on the page)

While the copilot works, the loading panel narrates the pipeline stages (routing → retrieval → guardrails → writing).

## UI overview

| Area | What it does |
|------|----------------|
| **Configuration panel (left)** | Agent mode + Top K slider |
| **Query input** | Your natural language question |
| **Suggestion chips** | One-click demo queries (submit on click) |
| **Answer panel** | Markdown answer with inline citations |
| **Bridge brief panel** | Appears for management brief queries — 7 sections + Copy |
| **Metrics row** | Confidence meter, agent badge, latency |
| **Guardrail banners** | Blue = outside the knowledge base · Red = blocked by security · Amber = low-confidence escalation |
| **Citations** | Clickable source cards with doc-type badges and SLA badges on tickets |
| **Source viewer** | Click any citation card to open the full verbatim source passage |
| **Agent trace** | Expandable JSON trace of routing, tools, guardrails, and (for Hindi) translation |

## Configuration options

### Agent mode

| Mode | When to use |
|------|-------------|
| **Auto** (default) | Let the system route factual vs analytical queries |
| **ReAct** | Force SOP/runbook style answers |
| **Plan Execute** | Force multi-step ticket/incident analysis |

### Top K sources (1–10)

Controls how many citation chunks are retrieved. Higher = more context, slightly slower.

## Example queries

### Factual (SOP / runbook)
- "How do I deploy a Kafka consumer?"
- "What are the Docker security runbook requirements?"
- "What is the VPN setup procedure?"

**Expected:** ReAct agent, SOP citations (violet badge), high confidence.

### Hindi / Hinglish
- "Kafka consumer कैसे deploy करें?"

**Expected:** The query is detected as Hindi, translated for retrieval, and answered in Hindi with technical terms kept in English — same SOP citations. The trace shows a `multilingual` block with the English query used internally. Allow a few extra seconds for the translation calls.

### Analytical (tickets)
- "Summarize all P1 deployment tickets this month"
- "List P2 database tickets"
- "Compare P1 and P2 deployment tickets"

**Expected:** Plan–Execute agent, ticket citations (blue badge).

### SLA proximity
- "Which P1 tickets are at risk of SLA breach?"
- "How many open tickets have breached SLA?"
- "List tickets within 1 hour of SLA breach"

**Expected:** Plan–Execute, SLA summary in answer, colored SLA badges on ticket citations:
- Green = On track
- Amber = At risk
- Red = Critical / Breached
- Gray = Resolved

### Incident bridge brief
- "Generate incident bridge brief for open P1 tickets"
- "Prepare incident bridge brief for open P1 network tickets"

**Expected:** Bridge brief panel with 7 sections. The executive summary opens with the incident count, SLA state, and affected services; model recommendations are prefixed "Recommended:". Click **Copy brief** for Slack/email. This is the slowest query type — the loading stages narrate the wait.

### Guardrails (try to break it)
- "What is the meaning of life?" → **blue banner**: outside the knowledge base. Honest low confidence, zero citations, escalated to a human, logged as a knowledge gap. No LLM call is made.
- "How do I hack the payroll database?" → **red banner**: blocked by the security guardrail in ~50 ms, logged, routed to security.

The copilot refuses rather than invents — ask it anything off-corpus and watch.

## Reading the answer

- Citations appear as `[1]`, `[2]` in the answer text
- **Click any citation card** to open the source viewer: the full verbatim passage, its relevance score, doc-type badge, and SLA badge
- **Overlap score** dot: green (strong), amber (moderate), red (weak)
- **Agent** badge shows which workflow ran (`react`, `plan_execute`, `bridge_brief`, or `guardrails` for refusals)

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| "Backend is still starting up" | Wait 2–3 minutes after a Railway deploy; the health dot turns green when ready |
| No citations | Rephrase query; increase Top K. (Refusals intentionally return zero citations.) |
| A legitimate query was refused | Lower `RELEVANCE_GATE_THRESHOLD` in Railway env vars (default 0.30) |
| Hindi query answered in English | Check `GET /health` shows `llm_ready: true` — translation needs a live LLM |
| Wrong agent | Switch Agent mode manually (ReAct vs Plan Execute) |
| SLA badges missing | Ask an SLA-specific query; ensure ticket citations returned |
| Bridge brief missing | Include words like "bridge brief" or "management call" |

## For administrators

- **Backend health:** `GET https://stepup-production-7453.up.railway.app/health`
- **Reindex data:** `python scripts/reingest_all.py` in Railway shell
- **Eval benchmark:** `python tests/run_ragas.py --api-url <backend-url>`
- **Tunables (Railway env vars):** `RELEVANCE_GATE_THRESHOLD`, `OPENROUTER_MODEL`, `CONFIDENCE_ESCALATION_THRESHOLD`

See [DEPLOYMENT.md](../DEPLOYMENT.md) and [DESIGN.md](DESIGN.md) for technical details.
