from __future__ import annotations

import re

from agents.llm import LLM_FAILURE_PREFIX, call_llm
from agents.sla_analytics import load_tickets_with_sla
from agents.tools import DocumentSearchTool, TicketLookupTool, extract_ticket_priority
from app.schemas import BridgeBriefSection, DocumentChunk, IncidentBridgeBrief
from retrieval.hybrid_retriever import HybridRetriever
from services.citations import build_citation_from_chunk


SECTION_HEADERS = {
    "executive_summary": ("Executive Summary", "## Executive Summary"),
    "impact": ("Customer / Business Impact", "## Customer / Business Impact"),
    "timeline": ("Timeline", "## Timeline"),
    "current_actions": ("Actions in Progress", "## Actions in Progress"),
    "customer_comms": ("Customer Communications", "## Customer Communications"),
    "decisions_needed": ("Decisions Needed", "## Decisions Needed"),
    "next_update": ("Next Update", "## Next Update"),
}


def is_bridge_brief_query(query: str) -> bool:
    q = query.lower()
    return any(
        keyword in q
        for keyword in (
            "bridge brief",
            "bridge call",
            "management call",
            "executive brief",
            "war room",
            "status update for leadership",
            "incident bridge",
            "leadership update",
        )
    )


def _bullets_from_text(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullets: list[str] = []
    for line in lines:
        cleaned = re.sub(r"^[-*•\d.)]+\s*", "", line).strip()
        if cleaned and not cleaned.startswith("#"):
            bullets.append(cleaned)
    return bullets[:6] if bullets else [text.strip()] if text.strip() else ["No data available."]


def _extract_section(markdown: str, header: str) -> str:
    pattern = re.compile(
        rf"{re.escape(header)}\s*\n(.*?)(?=\n## |\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(markdown)
    if not match:
        return ""
    return match.group(1).strip()


def _section(title: str, content: str) -> BridgeBriefSection:
    return BridgeBriefSection(title=title, bullets=_bullets_from_text(content))


def _fallback_brief(query: str, chunks: list[DocumentChunk]) -> IncidentBridgeBrief:
    ticket_chunks = [chunk for chunk in chunks if chunk.metadata.get("doc_type") == "ticket"]
    top_ticket = ticket_chunks[0] if ticket_chunks else None
    incident_id = top_ticket.metadata.get("source") if top_ticket else None
    severity = top_ticket.metadata.get("priority", "P1") if top_ticket else "P1"
    status = top_ticket.metadata.get("status", "Open") if top_ticket else "Open"

    ticket_lines = [
        f"{chunk.metadata.get('source')}: {chunk.text.splitlines()[0]}"
        for chunk in ticket_chunks[:5]
    ]
    if not ticket_lines:
        ticket_lines = ["No matching tickets found in indexed data."]

    return IncidentBridgeBrief(
        incident_id=incident_id,
        severity=severity,
        status=status,
        executive_summary=(
            f"Incident bridge brief prepared for: {query}. "
            f"{len(ticket_chunks)} ticket(s) retrieved from the knowledge base."
        ),
        impact=_section("Customer / Business Impact", "\n".join(ticket_lines)),
        timeline=_section(
            "Timeline",
            "\n".join(
                f"{ticket.metadata.get('source')} created {ticket.metadata.get('created_at', 'unknown')}"
                for ticket in ticket_chunks[:5]
            )
            or "Timeline details pending verification.",
        ),
        current_actions=_section(
            "Actions in Progress",
            "\n".join(
                f"{ticket.metadata.get('source')} — status {ticket.metadata.get('status', 'unknown')}"
                for ticket in ticket_chunks[:5]
            ),
        ),
        customer_comms=_section(
            "Customer Communications",
            "Status page update drafted. Customer-facing comms pending management approval.",
        ),
        decisions_needed=_section(
            "Decisions Needed",
            "Confirm escalation path, approve customer communication, and assign bridge owner.",
        ),
        next_update="Next leadership update in 30 minutes or upon material status change.",
    )


def _parse_brief(markdown: str, query: str, chunks: list[DocumentChunk]) -> IncidentBridgeBrief:
    ticket_chunks = [chunk for chunk in chunks if chunk.metadata.get("doc_type") == "ticket"]
    top_ticket = ticket_chunks[0] if ticket_chunks else None

    executive_summary = _extract_section(markdown, "## Executive Summary")
    if not executive_summary:
        executive_summary = markdown.strip()[:500] or f"Bridge brief for: {query}"

    next_update = _extract_section(markdown, "## Next Update")
    if not next_update:
        next_update = "Next leadership update in 30 minutes."

    return IncidentBridgeBrief(
        incident_id=top_ticket.metadata.get("source") if top_ticket else None,
        severity=top_ticket.metadata.get("priority", "P1") if top_ticket else "P1",
        status=top_ticket.metadata.get("status", "Open") if top_ticket else "Open",
        executive_summary=executive_summary.split("\n")[0][:500],
        impact=_section(
            "Customer / Business Impact",
            _extract_section(markdown, "## Customer / Business Impact"),
        ),
        timeline=_section("Timeline", _extract_section(markdown, "## Timeline")),
        current_actions=_section(
            "Actions in Progress",
            _extract_section(markdown, "## Actions in Progress"),
        ),
        customer_comms=_section(
            "Customer Communications",
            _extract_section(markdown, "## Customer Communications"),
        ),
        decisions_needed=_section(
            "Decisions Needed",
            _extract_section(markdown, "## Decisions Needed"),
        ),
        next_update=next_update.split("\n")[0][:300],
    )


class BridgeBriefTool:
    def __init__(self, retriever: HybridRetriever) -> None:
        self.ticket_lookup = TicketLookupTool(retriever)
        self.document_search = DocumentSearchTool(retriever)

    def run(self, query: str) -> dict:
        priority = extract_ticket_priority(query) or "P1"
        ticket_chunks = self.ticket_lookup.run(query)
        if not ticket_chunks:
            ticket_chunks = self.ticket_lookup.run(f"{priority} open incidents")

        doc_chunks = self.document_search.run(query)
        all_chunks = ticket_chunks + doc_chunks

        sla_tickets = load_tickets_with_sla()
        sla_context_lines = [
            f"{ticket.ticket_id} ({ticket.priority}) sla={ticket.sla.state if ticket.sla else 'unknown'} "
            f"remaining={ticket.sla.remaining_minutes if ticket.sla else 0}m"
            for ticket in sla_tickets
            if ticket.sla
            and ticket.sla.state in {"at_risk", "critical", "breached"}
            and (not priority or ticket.priority == priority)
        ][:8]

        context = "\n\n".join(
            f"[{index + 1}] {chunk.text[:700]}"
            for index, chunk in enumerate(all_chunks[:10])
        )
        sla_block = "\n".join(sla_context_lines) if sla_context_lines else "No at-risk SLA tickets."

        system_prompt = (
            "You are an enterprise incident commander preparing a management bridge brief. "
            "Use ONLY the provided ticket and SOP context for facts. Write concise "
            "executive language. Use the exact markdown section headers provided. "
            "Executive Summary: two to three complete sentences opening with the "
            "concrete numbers — how many incidents, their priority, how many have "
            "breached SLA, and which named services are affected. The count must "
            "match the incidents you list in the Timeline. Never open with vague "
            "phrases like 'multiple incidents' and never end with a lead-in such "
            "as 'as follows:'. "
            "Customer / Business Impact: one bullet per incident, naming the "
            "ticket ID and the specific service or user impact described in its "
            "ticket text. "
            "Timeline: one bullet per incident with its creation time and SLA "
            "state. Say 'SLA breached' rather than '0 minutes remaining'. "
            "Actions in Progress: state actions the context supports; if none are "
            "recorded, give the immediate next operational steps an incident "
            "commander would order, prefixed with 'Recommended:'. "
            "Customer Communications and Decisions Needed: if the context records "
            "nothing, provide your recommended communications and the specific "
            "decisions leadership should take now, each prefixed with "
            "'Recommended:'. Never write that nothing is needed. "
            "Next Update: always commit to a concrete cadence, e.g. 'Next update "
            "in 30 minutes or upon material change'."
        )
        prompt = (
            f"Context:\n{context}\n\n"
            f"SLA at-risk tickets:\n{sla_block}\n\n"
            f"Request: {query}\n\n"
            "Produce a management bridge brief with these exact sections:\n"
            "## Executive Summary\n"
            "## Customer / Business Impact\n"
            "## Timeline\n"
            "## Actions in Progress\n"
            "## Customer Communications\n"
            "## Decisions Needed\n"
            "## Next Update\n"
        )

        raw_answer = call_llm(prompt, system_prompt=system_prompt)
        retrieval_only = raw_answer.startswith(LLM_FAILURE_PREFIX)

        if retrieval_only:
            brief = _fallback_brief(query, all_chunks)
            answer = self._brief_to_markdown(brief)
        else:
            brief = _parse_brief(raw_answer, query, all_chunks)
            answer = raw_answer

        citations = [
            build_citation_from_chunk(chunk, rank)
            for rank, chunk in enumerate(all_chunks[:8])
        ]

        return {
            "answer": answer,
            "bridge_brief": brief,
            "citations": citations,
            "agent_used": "bridge_brief",
            "retrieval_only": retrieval_only,
            "trace": {
                "steps": [
                    {"step": "tool_call", "tool": "bridge_brief", "query": query},
                    {"step": "ticket_lookup", "chunks": len(ticket_chunks)},
                    {"step": "document_search", "chunks": len(doc_chunks)},
                ]
            },
        }

    def _brief_to_markdown(self, brief: IncidentBridgeBrief) -> str:
        sections = [
            ("## Executive Summary", brief.executive_summary),
            ("## Customer / Business Impact", "\n".join(f"- {b}" for b in brief.impact.bullets)),
            ("## Timeline", "\n".join(f"- {b}" for b in brief.timeline.bullets)),
            ("## Actions in Progress", "\n".join(f"- {b}" for b in brief.current_actions.bullets)),
            ("## Customer Communications", "\n".join(f"- {b}" for b in brief.customer_comms.bullets)),
            ("## Decisions Needed", "\n".join(f"- {b}" for b in brief.decisions_needed.bullets)),
            ("## Next Update", brief.next_update),
        ]
        return "\n\n".join(f"{header}\n{body}" for header, body in sections)
