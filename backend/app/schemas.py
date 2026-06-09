from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class AgentType(str, Enum):
    REACT = "react"
    PLAN_EXECUTE = "plan_execute"
    AUTO = "auto"


class OutputMode(str, Enum):
    DEFAULT = "default"
    BRIDGE_BRIEF = "bridge_brief"


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language question")
    top_k: int = Field(5, ge=1, le=20)
    force_agent: Optional[AgentType] = Field(None, description="Override auto-routing")
    session_id: Optional[str] = Field(None, description="Conversation memory key")
    output_mode: Optional[OutputMode] = Field(
        None, description="Optional structured output mode"
    )


class SlaStatus(BaseModel):
    state: str
    due_at: str
    remaining_minutes: int
    elapsed_pct: float = Field(ge=0.0, le=100.0)


class Citation(BaseModel):
    source_title: str
    source_url: str
    chunk_text: str
    overlap_score: float = Field(ge=0.0, le=1.0)
    doc_type: str
    sla: SlaStatus | None = None


class BridgeBriefSection(BaseModel):
    title: str
    bullets: list[str]


class IncidentBridgeBrief(BaseModel):
    incident_id: str | None = None
    severity: str
    status: str
    executive_summary: str
    impact: BridgeBriefSection
    timeline: BridgeBriefSection
    current_actions: BridgeBriefSection
    customer_comms: BridgeBriefSection
    decisions_needed: BridgeBriefSection
    next_update: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float = Field(ge=0.0, le=1.0)
    escalated: bool = False
    agent_used: str
    trace: dict
    retrieval_ms: int
    sla_summary: dict | None = None
    bridge_brief: IncidentBridgeBrief | None = None


class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    embedding: list[float] | None = None
    bm25_score: float | None = None
    rerank_score: float | None = None
    metadata: dict = {}
