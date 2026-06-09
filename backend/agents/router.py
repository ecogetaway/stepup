from __future__ import annotations
from app.schemas import AgentType
from app.config import settings


class QueryRouter:
    FACTUAL_KEYWORDS = frozenset(
        {
            "what", "how to", "how do", "where is", "when", "who",
            "document", "sop", "policy", "procedure", "define",
            "explain", "meaning of", "what is",
        }
    )
    ANALYTICAL_KEYWORDS = frozenset(
        {
            "summarise", "summarize", "compare", "trend", "analyse",
            "analyze", "why did", "p1", "p2", "p3", "tickets",
            "how many", "how much", "count", "breakdown",
            "last week", "this month", "report",
            "sla", "breach", "breached", "at risk", "due", "proximity", "within",
        }
    )
    BRIDGE_BRIEF_KEYWORDS = frozenset(
        {
            "bridge brief",
            "bridge call",
            "management call",
            "executive brief",
            "war room",
            "status update for leadership",
            "incident bridge",
            "leadership update",
        }
    )

    def is_bridge_brief(self, query: str) -> bool:
        q = query.lower()
        return any(keyword in q for keyword in self.BRIDGE_BRIEF_KEYWORDS)

    def route(self, query: str) -> AgentType:
        q = query.lower()
        analytical_hits = sum(1 for k in self.ANALYTICAL_KEYWORDS if k in q)
        factual_hits = sum(1 for k in self.FACTUAL_KEYWORDS if k in q)
        if analytical_hits > factual_hits:
            return AgentType.PLAN_EXECUTE
        if factual_hits > 0:
            return AgentType.REACT
        return AgentType.REACT
