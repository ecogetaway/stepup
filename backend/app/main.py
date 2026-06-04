from __future__ import annotations

import logging
import math
from contextlib import asynccontextmanager
from time import perf_counter

from agents.plan_execute_agent import PlanExecuteAgent
from agents.react_agent import ReActAgent
from agents.router import QueryRouter
from app.config import settings
from app.schemas import AgentType, Citation, QueryRequest, QueryResponse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from guardrails.confidence import ConfidenceScorer
from guardrails.escalation import EscalationEngine
from guardrails.hallucination_check import HallucinationChecker
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import Reranker

logger = logging.getLogger(__name__)


def _normalise_overlap_score(score: float | None) -> float:
    if score is None:
        return 0.0
    if 0.0 <= score <= 1.0:
        return float(score)
    return float(1.0 / (1.0 + math.exp(-score)))


def _build_citations(chunks) -> list[Citation]:
    citations: list[Citation] = []

    for chunk in chunks:
        citations.append(
            Citation(
                source_title=chunk.metadata.get("source", "unknown"),
                source_url=chunk.metadata.get("source_url", ""),
                chunk_text=chunk.text[:200],
                overlap_score=_normalise_overlap_score(chunk.rerank_score),
                doc_type=chunk.metadata.get("doc_type", "unknown"),
            )
        )

    return citations


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ready = False
    app.state.startup_error = None

    try:
        retriever = HybridRetriever()
        app.state.retriever = retriever
        app.state.reranker = Reranker()
        app.state.router = QueryRouter()
        app.state.react_agent = ReActAgent(retriever)
        app.state.plan_execute_agent = PlanExecuteAgent(retriever)
        app.state.hallucination_checker = HallucinationChecker()
        app.state.confidence_scorer = ConfidenceScorer()
        app.state.escalation_engine = EscalationEngine()
        app.state.ready = True
    except Exception as exc:
        logger.exception("Backend initialization failed")
        app.state.startup_error = str(exc)

    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.APP_ENV}


@app.post(f"{settings.API_V1_PREFIX}/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    if not app.state.ready:
        detail = app.state.startup_error or "Backend is not ready. Run ingestion first."
        raise HTTPException(status_code=503, detail=detail)

    started_at = perf_counter()
    forced_agent = request.force_agent
    agent_type = (
        forced_agent
        if forced_agent is not None and forced_agent != AgentType.AUTO
        else app.state.router.route(request.query)
    )

    chunks = app.state.retriever.retrieve(request.query)
    reranked_chunks = app.state.reranker.rerank(request.query, chunks, top_k=request.top_k)
    citations = _build_citations(reranked_chunks)

    if agent_type == AgentType.PLAN_EXECUTE:
        agent_result = app.state.plan_execute_agent.run(request.query)
    else:
        agent_result = app.state.react_agent.run(request.query)

    answer = agent_result["answer"]
    hallucination_flag, coverage_score = app.state.hallucination_checker.check(
        answer,
        citations,
    )
    confidence = app.state.confidence_scorer.score(
        citations,
        hallucination_flag=hallucination_flag,
        coverage_score=coverage_score,
    )
    escalated = app.state.confidence_scorer.should_escalate(confidence)
    retrieval_ms = int((perf_counter() - started_at) * 1000)

    trace = {
        **agent_result.get("trace", {}),
        "routing": {
          "forced_agent": forced_agent.value if forced_agent else None,
          "selected_agent": agent_type.value,
        },
        "retrieval": {
            "initial_chunks": len(chunks),
            "reranked_chunks": len(reranked_chunks),
            "top_k": request.top_k,
        },
        "guardrails": {
            "hallucination_flag": hallucination_flag,
            "coverage_score": coverage_score,
            "confidence": confidence,
            "escalated": escalated,
        },
    }

    response = QueryResponse(
        answer=answer,
        citations=citations,
        confidence=confidence,
        escalated=escalated,
        agent_used=agent_result.get("agent_used", agent_type.value),
        trace=trace,
        retrieval_ms=retrieval_ms,
    )
    return app.state.escalation_engine.apply(response)
