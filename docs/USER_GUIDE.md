# Enterprise Knowledge Copilot — User Guide

**Live app:** https://stepupcopilot.netlify.app  
**Team:** Vipers

## Who is this for?

- **L1/L2 support engineers** — find SOP steps and related tickets quickly  
- **Incident commanders** — summarize P1/P2 tickets and check SLA risk  
- **Managers / bridge call leads** — generate structured incident briefs  
- **New hires** — onboard faster with cited answers from internal docs  

## Getting started

1. Open https://stepupcopilot.netlify.app  
2. Wait for the header health indicator to show the backend is connected  
3. Pick a suggestion chip or type your own question  
4. Press **Ask** or `Cmd+Enter` / `Ctrl+Enter`  

## UI overview

| Area | What it does |
|------|----------------|
| **Configuration panel (left)** | Agent mode + Top K slider |
| **Query input** | Your natural language question |
| **Suggestion chips** | One-click demo queries |
| **Answer panel** | Markdown answer with inline citations |
| **Bridge brief panel** | Appears for management brief queries — 7 sections + Copy |
| **Metrics row** | Confidence meter, agent badge, latency |
| **Escalation banner** | Shows when human review is recommended |
| **Citations** | Source cards with doc-type badges and SLA badges on tickets |
| **Agent trace** | Expandable JSON trace of routing, tools, guardrails |

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

**Expected:** Bridge brief panel with 7 sections. Click **Copy brief** for Slack/email.

### Edge / refusal
- "What is the meaning of life?"
- "How do I hack the payroll database?"

**Expected:** Low confidence or refusal, escalation banner may appear.

## Reading the answer

- Citations appear as `[1]`, `[2]` in the answer text  
- Scroll to **Citations** to see full source excerpts  
- **Overlap score** dot: green (strong), amber (moderate), red (weak)  
- **Agent** badge shows which workflow ran (`react`, `plan_execute`, `bridge_brief`)

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| "Backend is not ready" | Wait 2–3 minutes after Railway deploy, refresh page |
| No citations | Rephrase query; increase Top K |
| Wrong agent | Switch Agent mode manually (ReAct vs Plan Execute) |
| SLA badges missing | Ask an SLA-specific query; ensure ticket citations returned |
| Bridge brief missing | Include words like "bridge brief" or "management call" |

## For administrators

- **Backend health:** `GET https://stepup-production-7453.up.railway.app/health`  
- **Reindex data:** `python scripts/reingest_all.py` in Railway shell  
- **Eval benchmark:** `python tests/run_ragas.py --api-url <backend-url>`  

See [DEPLOYMENT.md](../DEPLOYMENT.md) and [DESIGN.md](DESIGN.md) for technical details.
