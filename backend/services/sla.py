from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

SlaState = Literal["ok", "at_risk", "critical", "breached", "resolved"]

SLA_HOURS_BY_PRIORITY: dict[str, int] = {
    "P1": 4,
    "P2": 8,
    "P3": 24,
}

RESOLVED_STATUSES = frozenset({"resolved", "closed"})


@dataclass(frozen=True)
class SlaComputation:
    state: SlaState
    sla_due_at: datetime
    elapsed_pct: float
    remaining_minutes: int
    sla_hours: int


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _normalize_priority(priority: str) -> str:
    cleaned = (priority or "").strip().upper()
    if cleaned in SLA_HOURS_BY_PRIORITY:
        return cleaned
    return "P3"


def _normalize_status(status: str) -> str:
    return (status or "").strip().lower()


def compute_sla_state(
    created_at: str,
    priority: str,
    status: str,
    now: datetime | None = None,
) -> SlaComputation | None:
    created = _parse_datetime(created_at)
    if created is None:
        return None

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    normalized_status = _normalize_status(status)
    normalized_priority = _normalize_priority(priority)
    sla_hours = SLA_HOURS_BY_PRIORITY[normalized_priority]
    sla_due_at = created + timedelta(hours=sla_hours)

    if normalized_status in RESOLVED_STATUSES:
        return SlaComputation(
            state="resolved",
            sla_due_at=sla_due_at,
            elapsed_pct=0.0,
            remaining_minutes=0,
            sla_hours=sla_hours,
        )

    elapsed_seconds = max(0.0, (current - created).total_seconds())
    total_seconds = max(1.0, sla_hours * 3600)
    elapsed_pct = min(100.0, (elapsed_seconds / total_seconds) * 100.0)
    remaining_seconds = max(0.0, (sla_due_at - current).total_seconds())
    remaining_minutes = int(remaining_seconds // 60)

    if current >= sla_due_at:
        state: SlaState = "breached"
    elif elapsed_pct >= 90.0:
        state = "critical"
    elif elapsed_pct >= 75.0:
        state = "at_risk"
    else:
        state = "ok"

    return SlaComputation(
        state=state,
        sla_due_at=sla_due_at,
        elapsed_pct=round(elapsed_pct, 1),
        remaining_minutes=remaining_minutes,
        sla_hours=sla_hours,
    )


def sla_to_metadata(sla: SlaComputation) -> dict[str, str | int | float]:
    return {
        "sla_status": sla.state,
        "sla_due_at": sla.sla_due_at.isoformat(timespec="seconds"),
        "sla_remaining_minutes": sla.remaining_minutes,
        "sla_elapsed_pct": sla.elapsed_pct,
        "sla_hours": sla.sla_hours,
    }
