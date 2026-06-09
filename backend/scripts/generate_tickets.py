from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import settings

TICKETS_CSV = settings.TICKET_CSV

PRIORITIES = ["P1", "P2", "P3"]
STATUSES = ["Open", "In Progress", "Pending User", "Resolved", "Closed"]
CATEGORIES = ["Auth", "Database", "Deployment", "Network", "Access"]

TICKET_TEMPLATES = {
    "Auth": [
        "SSO login failures after identity provider metadata refresh",
        "MFA push approval delayed for remote users",
        "Service account token expired during overnight job",
        "OAuth redirect mismatch for internal admin console",
        "Password reset emails delayed for contractor accounts",
    ],
    "Database": [
        "Read replica lag causing stale dashboard values",
        "Connection pool exhaustion on customer analytics service",
        "Slow query detected on incidents reporting table",
        "Backup verification failed for finance PostgreSQL cluster",
        "Schema migration lock observed during release window",
    ],
    "Deployment": [
        "Canary deployment failed readiness probe in staging",
        "Kafka consumer rollout stuck after config map update",
        "Container image rejected by vulnerability admission policy",
        "Blue green deployment did not shift traffic as expected",
        "Rollback needed after elevated API error rate",
    ],
    "Network": [
        "VPN users unable to resolve internal DNS zone",
        "Packet loss detected between application subnet and database subnet",
        "Firewall rule missing for vendor integration endpoint",
        "Load balancer health checks failing from one region",
        "TLS handshake failures on internal service mesh route",
    ],
    "Access": [
        "User needs production read-only access for incident review",
        "Quarterly access recertification missing application owner approval",
        "Contractor access group expired before project completion",
        "Privileged role request requires emergency approval",
        "Shared drive permissions not synced from identity group",
    ],
}


def priority_for_ticket(index: int) -> str:
    if index in {4, 11, 18, 27, 36, 44}:
        return "P1"
    if index % 3 == 0 or index % 5 == 0:
        return "P2"
    return "P3"


def build_description(priority: str, category: str, subject: str, index: int) -> str:
    impact = {
        "P1": "Customer-facing impact reported by multiple business units. Immediate triage bridge required.",
        "P2": "Service degradation reported by an internal team. Workaround may exist but needs owner confirmation.",
        "P3": "Routine support request or localized issue. Handle through normal queue prioritization.",
    }[priority]
    evidence = (
        f"Initial evidence includes category={category}, ticket sequence {index:02d}, "
        "recent deployment history, monitoring alerts, and user-provided screenshots where available."
    )
    return f"{subject}. {impact} {evidence}"


def created_at_for_ticket(index: int, priority: str, now: datetime) -> datetime:
    """Spread timestamps so open P1 tickets show ok / at-risk / breached at demo time."""
    if priority == "P1":
        p1_offsets = {
            4: timedelta(hours=1),    # ok — 25% of 4h SLA
            11: timedelta(hours=3, minutes=30),  # at_risk — ~87.5%
            18: timedelta(hours=5),   # breached (resolved in CSV)
            27: timedelta(hours=3, minutes=45),  # critical
            36: timedelta(hours=4, minutes=15),  # breached
            44: timedelta(hours=2, minutes=30),  # at_risk
        }
        return now - p1_offsets.get(index, timedelta(hours=2))

    if priority == "P2":
        return now - timedelta(hours=4 + (index % 5))

    return now - timedelta(hours=8 + (index % 12))


def status_for_ticket(index: int, priority: str) -> str:
    if index == 18:
        return "Resolved"
    if priority == "P1" and index in {4, 11, 27, 36, 44}:
        return "Open" if index in {11, 27, 36, 44} else "In Progress"
    return STATUSES[(index + len(priority)) % len(STATUSES)]


def generate_rows() -> list[dict[str, str]]:
    now = datetime(2026, 6, 9, 10, 0)
    rows: list[dict[str, str]] = []

    for index in range(1, 51):
        category = CATEGORIES[(index - 1) % len(CATEGORIES)]
        subject = TICKET_TEMPLATES[category][(index - 1) // len(CATEGORIES) % 5]
        priority = priority_for_ticket(index)
        status = status_for_ticket(index, priority)
        created_at = created_at_for_ticket(index, priority, now)

        rows.append(
            {
                "id": f"TCK-{20260600 + index}",
                "priority": priority,
                "subject": subject,
                "description": build_description(priority, category, subject, index),
                "status": status,
                "category": category,
                "created_at": created_at.isoformat(timespec="seconds"),
            }
        )

    return rows


def main() -> None:
    TICKETS_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_rows()

    with TICKETS_CSV.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "id",
                "priority",
                "subject",
                "description",
                "status",
                "category",
                "created_at",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} tickets at {TICKETS_CSV}")


if __name__ == "__main__":
    main()
