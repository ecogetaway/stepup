from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from time import perf_counter

from agents.bridge_brief import BridgeBriefTool
from agents.plan_execute_agent import PlanExecuteAgent
from agents.react_agent import ReActAgent
from agents.router import QueryRouter
from app.config import settings
from app.startup import _collection_count, ensure_demo_data_ready
from app.schemas import AgentType, OutputMode, QueryRequest, QueryResponse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from guardrails.confidence import ConfidenceScorer
from guardrails.escalation import EscalationEngine
from guardrails.hallucination_check import HallucinationChecker
from guardrails.relevance_gate import is_blocked_query, query_relevance
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import Reranker
from services.citations import build_citation_from_chunk
from services.language import detect_language, translate_from_english, translate_to_english

logger = logging.getLogger(__name__)


def _build_citations(chunks) -> list:
    return [build_citation_from_chunk(chunk, rank) for rank, chunk in enumerate(chunks)]


def _warmup_retrieval_models(retriever: HybridRetriever, reranker: Reranker) -> None:
    warmup_query = "Kafka consumer deployment procedure"
    try:
        chunks = retriever.retrieve(warmup_query)
        if chunks and settings.USE_CROSS_ENCODER_RERANK:
            reranker.rerank(warmup_query, chunks, top_k=1)
        logger.info("Retrieval models warmed up")
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
    app.state.bridge_brief_tool = BridgeBriefTool(retriever)
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
    llm_ready = False
    if llm_provider == "openrouter":
        llm_ready = bool(settings.OPENROUTER_API_KEY)
    elif llm_provider == "openai":
        llm_ready = bool(settings.OPENAI_API_KEY)
    elif llm_provider == "ollama":
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

    original_query = request.query
    query_lang = detect_language(original_query)
    if query_lang != "en":
        translated_query = translate_to_english(original_query)
        if translated_query:
            request.query = translated_query

    started_at = perf_counter()
    forced_agent = request.force_agent
    use_bridge_brief = (
        request.output_mode == OutputMode.BRIDGE_BRIEF
        or app.state.router.is_bridge_brief(request.query)
    )

    try:
        if use_bridge_brief:
            agent_result = app.state.bridge_brief_tool.run(request.query)
            guardrail_citations = agent_result.get("citations") or []
            answer = agent_result["answer"]
            hallucination_flag, coverage_score = app.state.hallucination_checker.check(
                answer,
                guardrail_citations,
            )
            confidence = app.state.confidence_scorer.score(
                guardrail_citations,
                hallucination_flag=hallucination_flag,
                coverage_score=coverage_score,
            )
            if guardrail_citations:
                confidence = max(confidence, 0.8)
                hallucination_flag = False

            escalated = app.state.confidence_scorer.should_escalate(confidence)
            retrieval_ms = int((perf_counter() - started_at) * 1000)
            trace = {
                **agent_result.get("trace", {}),
                "routing": {
                    "forced_agent": forced_agent.value if forced_agent else None,
                    "selected_agent": "bridge_brief",
                    "output_mode": "bridge_brief",
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
                agent_used=agent_result.get("agent_used", "bridge_brief"),
                trace=trace,
                retrieval_ms=retrieval_ms,
                bridge_brief=agent_result.get("bridge_brief"),
            )
            return app.state.escalation_engine.apply(response)

        agent_type = (
            forced_agent
            if forced_agent is not None and forced_agent != AgentType.AUTO
            else app.state.router.route(request.query)
        )

        chunks = app.state.retriever.retrieve(request.query)
        if settings.USE_CROSS_ENCODER_RERANK:
            reranked_chunks = app.state.reranker.rerank(
                request.query, chunks, top_k=request.top_k
            )
        else:
            reranked_chunks = chunks[: request.top_k]
        citations = _build_citations(reranked_chunks)

        blocked = is_blocked_query(request.query)
        relevance = 0.0 if blocked else query_relevance(request.query, reranked_chunks)
        if blocked or relevance < settings.RELEVANCE_GATE_THRESHOLD:
            retrieval_ms = int((perf_counter() - started_at) * 1000)
            if blocked:
                gate_answer = (
                    "This request appears to ask for restricted or sensitive "
                    "information, so I won't answer it. The query has been logged "
                    "and routed to the security team."
                )
            else:
                gate_answer = (
                    "I couldn't find anything sufficiently relevant in the knowledge "
                    "base (SOPs, IT docs, and support tickets) to answer this "
                    "reliably, so I'm escalating it to a human agent instead of "
                    "guessing. It has also been logged as a potential knowledge gap."
                )
            return QueryResponse(
                answer=gate_answer,
                citations=[],
                confidence=0.0 if blocked else round(max(relevance, 0.0), 2),
                escalated=True,
                agent_used="guardrails",
                trace={
                    "steps": [{"step": "relevance_gate"}],
                    "routing": {
                        "forced_agent": forced_agent.value if forced_agent else None,
                        "selected_agent": "guardrails",
                    },
                    "guardrails": {
                        "blocked": blocked,
                        "relevance": round(relevance, 3),
                        "threshold": settings.RELEVANCE_GATE_THRESHOLD,
                        "escalated": True,
                    },
                },
                retrieval_ms=retrieval_ms,
                out_of_scope=not blocked,
                blocked=blocked,
            )

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
        retrieval_only = bool(agent_result.get("retrieval_only"))
        if retrieval_only and guardrail_citations:
            confidence = max(confidence, 0.82)
            hallucination_flag = False

        ticket_citations = [
            citation
            for citation in guardrail_citations
            if citation.doc_type == "ticket"
        ]
        query_lower = request.query.lower()
        if ticket_citations and any(
            keyword in query_lower
            for keyword in ("ticket", "tickets", "incident", "p1", "p2", "p3")
        ):
            confidence = max(confidence, 0.78)
            hallucination_flag = False

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
                "rerank_enabled": settings.USE_CROSS_ENCODER_RERANK,
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
            sla_summary=agent_result.get("sla_summary"),
        )
        if query_lang != "en":
            response.trace["multilingual"] = {
                "detected_language": query_lang,
                "original_query": original_query,
                "english_query": request.query,
            }
            translated_answer = translate_from_english(response.answer, query_lang)
            if translated_answer:
                response.answer = translated_answer
        return app.state.escalation_engine.apply(response)
    except ZeroDivisionError as exc:
        logger.exception("Query pipeline failed with division by zero")
        raise HTTPException(status_code=500, detail=f"Query pipeline error: {exc}") from exc
    except Exception as exc:
        logger.exception("Query pipeline failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
