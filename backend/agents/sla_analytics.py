from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from app.config import settings
from services.sla import SlaComputation, compute_sla_state


@dataclass
class TicketWithSla:
    ticket_id: str
    priority: str
    category: str
    subject: str
    status: str
    created_at: str
    sla: SlaComputation | None


def is_sla_query(query: str) -> bool:
    q = query.lower()
    return any(
        keyword in q
        for keyword in (
            "sla",
            "breach",
            "breached",
            "at risk",
            "at-risk",
            "due",
            "proximity",
            "within",
            "time to breach",
        )
    )


def load_tickets_with_sla(now: datetime | None = None) -> list[TicketWithSla]:
    path = settings.TICKET_CSV
    if not path.exists():
        return []

    tickets: list[TicketWithSla] = []
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            ticket_id = (row.get("id") or "").strip()
            if not ticket_id:
                continue
            priority = (row.get("priority") or "").strip()
            category = (row.get("category") or "").strip()
            subject = (row.get("subject") or "").strip()
            status = (row.get("status") or "").strip()
            created_at = (row.get("created_at") or "").strip()
            sla = compute_sla_state(created_at, priority, status, now=now)
            tickets.append(
                TicketWithSla(
                    ticket_id=ticket_id,
                    priority=priority,
                    category=category,
                    subject=subject,
                    status=status,
                    created_at=created_at,
                    sla=sla,
                )
            )
    return tickets


def _extract_priority(query: str) -> str | None:
    match = re.search(r"\bp([123])\b", query.lower())
    if not match:
        return None
    return f"P{match.group(1)}"


def _extract_category(query: str) -> str | None:
    q = query.lower()
    for category in ("auth", "database", "deployment", "network", "access"):
        if category in q:
            return category.title()
    return None


def _extract_within_hours(query: str) -> float | None:
    q = query.lower()
    hour_match = re.search(r"within\s+(\d+(?:\.\d+)?)\s+hour", q)
    if hour_match:
        return float(hour_match.group(1))
    minute_match = re.search(r"within\s+(\d+)\s+minute", q)
    if minute_match:
        return float(minute_match.group(1)) / 60.0
    if "1 hour" in q or "one hour" in q:
        return 1.0
    return None


def _is_open_status(status: str) -> bool:
    return status.strip().lower() not in {"resolved", "closed"}


def aggregate(query: str, now: datetime | None = None) -> dict:
    tickets = load_tickets_with_sla(now=now)
    q = query.lower()
    priority = _extract_priority(query)
    category = _extract_category(query)
    within_hours = _extract_within_hours(query)

    filtered: list[TicketWithSla] = []
    for ticket in tickets:
        if priority and ticket.priority != priority:
            continue
        if category and ticket.category.lower() != category.lower():
            continue
        if "open" in q and not _is_open_status(ticket.status):
            continue
        if ticket.sla is None:
            continue

        sla_state = ticket.sla.state
        at_risk_query = "at risk" in q or "at-risk" in q
        breach_query = (
            "breached" in q
            or ("breach" in q and not at_risk_query and "sla breach?" not in q)
            or "past sla" in q
        )
        if at_risk_query:
            if sla_state not in {"at_risk", "critical"}:
                continue
        elif breach_query and sla_state != "breached":
            continue
        if "critical" in q and not at_risk_query and sla_state != "critical":
            continue
        if within_hours is not None:
            remaining_hours = ticket.sla.remaining_minutes / 60.0
            if sla_state in {"breached", "resolved"} or remaining_hours > within_hours:
                continue

        filtered.append(ticket)

    if not filtered and not any(
        keyword in q
        for keyword in ("breach", "at risk", "at-risk", "critical", "within", "open")
    ):
        filtered = [
            ticket
            for ticket in tickets
            if ticket.sla is not None
            and (not priority or ticket.priority == priority)
            and (not category or ticket.category.lower() == category.lower())
            and (_is_open_status(ticket.status) if "open" in q else True)
        ]

    counts_by_state: dict[str, int] = {}
    counts_by_priority: dict[str, int] = {}
    for ticket in filtered:
        if ticket.sla is None:
            continue
        counts_by_state[ticket.sla.state] = counts_by_state.get(ticket.sla.state, 0) + 1
        counts_by_priority[ticket.priority] = counts_by_priority.get(ticket.priority, 0) + 1

    top_tickets = [
        {
            "ticket_id": ticket.ticket_id,
            "priority": ticket.priority,
            "category": ticket.category,
            "status": ticket.status,
            "subject": ticket.subject,
            "sla_state": ticket.sla.state if ticket.sla else "unknown",
            "remaining_minutes": ticket.sla.remaining_minutes if ticket.sla else 0,
            "elapsed_pct": ticket.sla.elapsed_pct if ticket.sla else 0.0,
        }
        for ticket in sorted(
            filtered,
            key=lambda item: (
                0
                if item.sla and item.sla.state == "breached"
                else 1
                if item.sla and item.sla.state == "critical"
                else 2
                if item.sla and item.sla.state == "at_risk"
                else 3,
                -(item.sla.elapsed_pct if item.sla else 0.0),
            ),
        )[:10]
    ]

    return {
        "query": query,
        "generated_at": (now or datetime.now(timezone.utc)).isoformat(),
        "total_matched": len(filtered),
        "counts_by_state": counts_by_state,
        "counts_by_priority": counts_by_priority,
        "top_tickets": top_tickets,
        "filters": {
            "priority": priority,
            "category": category,
            "within_hours": within_hours,
        },
    }


def format_sla_context(summary: dict) -> str:
    lines = [
        "Deterministic SLA analytics (computed from ticket CSV):",
        f"- Total matched tickets: {summary['total_matched']}",
    ]
    if summary["counts_by_state"]:
        state_parts = ", ".join(
            f"{state}={count}" for state, count in sorted(summary["counts_by_state"].items())
        )
        lines.append(f"- Counts by SLA state: {state_parts}")
    if summary["counts_by_priority"]:
        priority_parts = ", ".join(
            f"{priority}={count}"
            for priority, count in sorted(summary["counts_by_priority"].items())
        )
        lines.append(f"- Counts by priority: {priority_parts}")
    if summary["top_tickets"]:
        lines.append("- Top tickets:")
        for ticket in summary["top_tickets"]:
            lines.append(
                f"  * {ticket['ticket_id']} ({ticket['priority']}, {ticket['category']}) "
                f"status={ticket['status']} sla={ticket['sla_state']} "
                f"remaining={ticket['remaining_minutes']}m elapsed={ticket['elapsed_pct']}% "
                f"subject={ticket['subject']}"
            )
    return "\n".join(lines)
