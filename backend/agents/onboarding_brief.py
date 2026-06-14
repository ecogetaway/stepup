from __future__ import annotations

import re

from agents.llm import LLM_FAILURE_PREFIX, call_llm
from agents.tools import DocumentSearchTool, TicketLookupTool
from app.schemas import BridgeBriefSection, DocumentChunk, OnboardingBrief
from retrieval.hybrid_retriever import HybridRetriever
from services.citations import build_citation_from_chunk


# Broad-by-design seed queries so the brief covers the whole onboarding
# surface (all SOPs + a spread of recurring ticket categories) regardless
# of how narrowly the user's own question is phrased.
SOP_SEED_QUERIES = [
    "Kafka consumer and producer deployment procedure",
    "Docker security runbook requirements",
    "VPN remote access setup procedure",
]
TICKET_SEED_QUERIES = [
    "Kafka deployment rollout issue",
    "VPN network access issue",
    "service account authentication issue",
]

ROLE_PATTERNS: list[tuple[str, str]] = [
    (r"devops", "DevOps Engineer"),
    (r"platform engineer", "Platform Engineer"),
    (r"site reliability|\bsre\b", "Site Reliability Engineer"),
    (r"network", "Network Support Engineer"),
    (r"security", "Security Support Engineer"),
    (r"application support|app support", "Application Support Engineer"),
]
DEFAULT_ROLE = "Application Support Engineer"


def extract_role(query: str) -> str:
    q = query.lower()
    for pattern, label in ROLE_PATTERNS:
        if re.search(pattern, q):
            return label
    return DEFAULT_ROLE


def _bullets_from_text(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullets: list[str] = []
    for line in lines:
        cleaned = re.sub(r"^[-*•\d.)]+\s*", "", line).strip()
        if cleaned and not cleaned.startswith("#"):
            bullets.append(cleaned)
    return bullets[:8] if bullets else [text.strip()] if text.strip() else ["No data available."]


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


def _dedupe_chunks(chunks: list[DocumentChunk]) -> list[DocumentChunk]:
    seen: set[str] = set()
    deduped: list[DocumentChunk] = []
    for chunk in chunks:
        if chunk.chunk_id in seen:
            continue
        seen.add(chunk.chunk_id)
        deduped.append(chunk)
    return deduped


def _fallback_brief(role: str, sop_chunks: list[DocumentChunk], ticket_chunks: list[DocumentChunk]) -> OnboardingBrief:
    sop_lines = [
        f"{chunk.metadata.get('source', 'document')}: {chunk.text.splitlines()[0][:160]}"
        for chunk in sop_chunks[:6]
    ] or ["No SOPs found in the knowledge base."]

    ticket_lines = [
        f"{chunk.metadata.get('source')}: {chunk.text.splitlines()[0][:160]}"
        for chunk in ticket_chunks[:6]
    ] or ["No recent tickets found in the knowledge base."]

    return OnboardingBrief(
        role_focus=role,
        welcome_summary=(
            f"Welcome! This brief was prepared for a {role.lower()} using the "
            f"SOPs and tickets currently in the knowledge base."
        ),
        key_systems=_section("Key Systems & Documentation", "\n".join(sop_lines)),
        common_issues=_section("Common Issues to Know About", "\n".join(ticket_lines)),
        tools_and_access=_section(
            "Tools & Access Setup",
            "Review the VPN remote access SOP for connectivity requirements.",
        ),
        who_to_ask=_section(
            "Who to Ask",
            "Refer to each SOP's scope section for the owning team before escalating.",
        ),
        first_week_checklist=_section(
            "First Week Checklist",
            "\n".join(
                [
                    "Read each SOP listed under Key Systems & Documentation.",
                    "Set up VPN and tooling access per the VPN SOP.",
                    "Review the tickets listed under Common Issues to Know About.",
                    "Ask this copilot any SOP or ticket question as it comes up.",
                ]
            ),
        ),
        additional_resources=(
            "Use this copilot for any follow-up question — ask about specific "
            "SOPs, tickets, or SLA status as you ramp up."
        ),
    )


def _parse_brief(markdown: str, role: str) -> OnboardingBrief:
    welcome_summary = _extract_section(markdown, "## Welcome Summary")
    if not welcome_summary:
        welcome_summary = markdown.strip()[:500] or f"Onboarding brief for a {role.lower()}."

    additional_resources = _extract_section(markdown, "## Additional Resources")
    if not additional_resources:
        additional_resources = (
            "Use this copilot for any follow-up question as you ramp up."
        )

    return OnboardingBrief(
        role_focus=role,
        welcome_summary=welcome_summary.split("\n")[0][:500],
        key_systems=_section(
            "Key Systems & Documentation",
            _extract_section(markdown, "## Key Systems & Documentation"),
        ),
        common_issues=_section(
            "Common Issues to Know About",
            _extract_section(markdown, "## Common Issues to Know About"),
        ),
        tools_and_access=_section(
            "Tools & Access Setup",
            _extract_section(markdown, "## Tools & Access Setup"),
        ),
        who_to_ask=_section(
            "Who to Ask",
            _extract_section(markdown, "## Who to Ask"),
        ),
        first_week_checklist=_section(
            "First Week Checklist",
            _extract_section(markdown, "## First Week Checklist"),
        ),
        additional_resources=additional_resources.split("\n")[0][:300],
    )


class OnboardingBriefTool:
    def __init__(self, retriever: HybridRetriever) -> None:
        self.document_search = DocumentSearchTool(retriever)
        self.ticket_lookup = TicketLookupTool(retriever)

    def run(self, query: str) -> dict:
        role = extract_role(query)

        sop_chunks: list[DocumentChunk] = []
        for seed in SOP_SEED_QUERIES:
            sop_chunks.extend(self.document_search.run(seed))
        sop_chunks.extend(self.document_search.run(query))
        sop_chunks = _dedupe_chunks(sop_chunks)

        ticket_chunks: list[DocumentChunk] = []
        for seed in TICKET_SEED_QUERIES:
            ticket_chunks.extend(self.ticket_lookup.run(seed))
        ticket_chunks = _dedupe_chunks(ticket_chunks)

        all_chunks = sop_chunks[:6] + ticket_chunks[:6]

        context = "\n\n".join(
            f"[{index + 1}] {chunk.text[:700]}"
            for index, chunk in enumerate(all_chunks)
        )

        system_prompt = (
            f"You are preparing an onboarding brief for a new {role} joining an "
            "enterprise IT organization. Use ONLY the provided SOP and ticket "
            "context. Write in a welcoming, practical tone suited to someone on "
            "their first day. Use the exact markdown section headers provided.\n"
            "Welcome Summary: 2-3 sentences orienting the new hire to the systems "
            "and ticket categories covered by the context.\n"
            "Key Systems & Documentation: one bullet per SOP/document found in "
            "the context, naming it and summarizing what it covers and when to "
            "read it.\n"
            "Common Issues to Know About: summarize the recurring ticket patterns "
            "found in the context, so the new hire recognizes them when they see "
            "them. Name specific ticket IDs where useful.\n"
            "Tools & Access Setup: concrete setup steps drawn from the SOPs (for "
            "example VPN or deployment tooling access).\n"
            "Who to Ask: name the owning team(s) mentioned in the SOPs, mapped to "
            "the relevant system or category, for escalation.\n"
            "First Week Checklist: 5-8 concrete, numbered action items grounded in "
            "the provided context.\n"
            "Additional Resources: one or two lines pointing the new hire back to "
            "this copilot for follow-up questions.\n"
            "If the context does not support a section, say so briefly in one "
            "line rather than inventing specifics."
        )
        prompt = (
            f"Context:\n{context}\n\n"
            f"Request: {query}\n\n"
            "Produce an onboarding brief with these exact sections:\n"
            "## Welcome Summary\n"
            "## Key Systems & Documentation\n"
            "## Common Issues to Know About\n"
            "## Tools & Access Setup\n"
            "## Who to Ask\n"
            "## First Week Checklist\n"
            "## Additional Resources\n"
        )

        raw_answer = call_llm(prompt, system_prompt=system_prompt)
        retrieval_only = raw_answer.startswith(LLM_FAILURE_PREFIX)

        if retrieval_only:
            brief = _fallback_brief(role, sop_chunks, ticket_chunks)
            answer = self._brief_to_markdown(brief)
        else:
            brief = _parse_brief(raw_answer, role)
            answer = raw_answer

        citations = [
            build_citation_from_chunk(chunk, rank)
            for rank, chunk in enumerate(all_chunks[:8])
        ]

        return {
            "answer": answer,
            "onboarding_brief": brief,
            "citations": citations,
            "agent_used": "onboarding_brief",
            "retrieval_only": retrieval_only,
            "trace": {
                "steps": [
                    {"step": "tool_call", "tool": "onboarding_brief", "query": query, "role": role},
                    {"step": "document_search", "chunks": len(sop_chunks)},
                    {"step": "ticket_lookup", "chunks": len(ticket_chunks)},
                ]
            },
        }

    def _brief_to_markdown(self, brief: OnboardingBrief) -> str:
        sections = [
            ("## Welcome Summary", brief.welcome_summary),
            ("## Key Systems & Documentation", "\n".join(f"- {b}" for b in brief.key_systems.bullets)),
            ("## Common Issues to Know About", "\n".join(f"- {b}" for b in brief.common_issues.bullets)),
            ("## Tools & Access Setup", "\n".join(f"- {b}" for b in brief.tools_and_access.bullets)),
            ("## Who to Ask", "\n".join(f"- {b}" for b in brief.who_to_ask.bullets)),
            ("## First Week Checklist", "\n".join(f"- {b}" for b in brief.first_week_checklist.bullets)),
            ("## Additional Resources", brief.additional_resources),
        ]
        return "\n\n".join(f"{header}\n{body}" for header, body in sections)
