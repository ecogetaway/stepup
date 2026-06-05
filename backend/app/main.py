from __future__ import annotations

import asyncio
import logging
import math
import os
from contextlib import asynccontextmanager
from time import perf_counter

from agents.plan_execute_agent import PlanExecuteAgent
from agents.react_agent import ReActAgent
from agents.router import QueryRouter
from app.config import settings
from app.startup import _collection_count, ensure_demo_data_ready
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
    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(numeric_score) or math.isinf(numeric_score):
        return 0.0
    if 0.0 <= numeric_score <= 1.0:
        return numeric_score
    return float(1.0 / (1.0 + math.exp(-numeric_score)))


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


def _warmup_retrieval_models(retriever: HybridRetriever, reranker: Reranker) -> None:
    warmup_query = "Kafka consumer deployment procedure"
    try:
        chunks = retriever.retrieve(warmup_query)
        if chunks:
            reranker.rerank(warmup_query, chunks, top_k=1)
        logger.info("Retrieval and reranker models warmed up")
    except Exception:
        logger.exception("Model warmup failed; first query may be slower")


def _bootstrap_app_state(app: FastAPI) -> None:
    ensure_demo_data_ready()
    retriever = HybridRetriever()
    reranker = Reranker()
    _warmup_retrieval_models(retriever, reranker)
    app.state.retriever = retriever
    app.state.reranker = reranker
    app.state.router = QueryRouter()
    app.state.react_agent = ReActAgent(retriever)
    app.state.plan_execute_agent = PlanExecuteAgent(retriever)
    app.state.hallucination_checker = HallucinationChecker()
    app.state.confidence_scorer = ConfidenceScorer()
    app.state.escalation_engine = EscalationEngine()
    app.state.ready = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ready = False
    app.state.startup_error = None
    app.state.bootstrap_running = True

    async def bootstrap() -> None:
        try:
            await asyncio.to_thread(_bootstrap_app_state, app)
            logger.info("Backend bootstrap completed")
        except Exception as exc:
            logger.exception("Backend initialization failed")
            app.state.startup_error = str(exc)
        finally:
            app.state.bootstrap_running = False

    bootstrap_task = asyncio.create_task(bootstrap())

    yield

    bootstrap_task.cancel()
    try:
        await bootstrap_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str | bool | int]:
    deploy_commit = (
        os.getenv("RAILWAY_GIT_COMMIT_SHA")
        or os.getenv("RAILWAY_GIT_COMMIT")
        or os.getenv("GIT_COMMIT_SHA")
        or os.getenv("GIT_COMMIT")
        or ""
    )
    llm_provider = settings.LLM_PROVIDER.strip().lower()
    llm_ready = llm_provider == "openrouter" and bool(settings.OPENROUTER_API_KEY)
    if llm_provider == "ollama":
        llm_ready = bool(settings.OLLAMA_BASE_URL)

    try:
        collection_count = _collection_count()
    except Exception:
        logger.exception("Failed to read Chroma collection count for health check")
        collection_count = None

    return {
        "status": "ok",
        "env": settings.APP_ENV,
        "commit": deploy_commit[:12],
        "ready": bool(getattr(app.state, "ready", False)),
        "bootstrap_running": bool(getattr(app.state, "bootstrap_running", False)),
        "llm_provider": llm_provider,
        "llm_ready": llm_ready,
        "collection_count": collection_count if collection_count is not None else -1,
    }


@app.post(f"{settings.API_V1_PREFIX}/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    if not app.state.ready:
        if app.state.startup_error:
            detail = app.state.startup_error
        elif getattr(app.state, "bootstrap_running", False):
            detail = "Backend is still starting up. Please wait 2-3 minutes and try again."
        else:
            detail = "Backend is not ready. Run ingestion first."
        raise HTTPException(status_code=503, detail=detail)

    started_at = perf_counter()
    forced_agent = request.force_agent
    agent_type = (
        forced_agent
        if forced_agent is not None and forced_agent != AgentType.AUTO
        else app.state.router.route(request.query)
    )

    try:
        chunks = app.state.retriever.retrieve(request.query)
        reranked_chunks = app.state.reranker.rerank(request.query, chunks, top_k=request.top_k)
        citations = _build_citations(reranked_chunks)

        if agent_type == AgentType.PLAN_EXECUTE:
            agent_result = app.state.plan_execute_agent.run(request.query)
        else:
            agent_result = app.state.react_agent.run(request.query, chunks=reranked_chunks)

        answer = agent_result["answer"]
        guardrail_citations = agent_result.get("citations") or citations
        hallucination_flag, coverage_score = app.state.hallucination_checker.check(
            answer,
            guardrail_citations,
        )
        confidence = app.state.confidence_scorer.score(
            guardrail_citations,
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
            citations=guardrail_citations,
            confidence=confidence,
            escalated=escalated,
            agent_used=agent_result.get("agent_used", agent_type.value),
            trace=trace,
            retrieval_ms=retrieval_ms,
        )
        return app.state.escalation_engine.apply(response)
    except ZeroDivisionError as exc:
        logger.exception("Query pipeline failed with division by zero")
        raise HTTPException(status_code=500, detail=f"Query pipeline error: {exc}") from exc
    except Exception as exc:
        logger.exception("Query pipeline failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
