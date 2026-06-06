from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

try:
    import httpx

    HAS_HTTPX = True
except ModuleNotFoundError:
    HAS_HTTPX = False


def load_golden_set(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("golden_qa.json must be a list of question objects")
    return data


def query_api(base_url: str, question: str, timeout: float) -> dict:
    if not HAS_HTTPX:
        raise ModuleNotFoundError("httpx is required. Install with: pip install httpx")

    response = httpx.post(
        f"{base_url.rstrip('/')}/api/v1/query",
        json={"query": question, "top_k": 5},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def token_overlap(answer: str, ground_truth: str) -> float:
    answer_tokens = set(re.findall(r"[a-z0-9]+", answer.lower()))
    truth_tokens = set(re.findall(r"[a-z0-9]+", ground_truth.lower()))
    if not truth_tokens:
        return 0.0
    return len(answer_tokens & truth_tokens) / len(truth_tokens)


def run_baseline_metrics(
    base_url: str,
    golden_set: list[dict],
    timeout: float,
    limit: int | None,
) -> dict:
    rows: list[dict] = []
    subset = golden_set[:limit] if limit else golden_set

    for item in subset:
        question = item["question"]
        ground_truth = item.get("ground_truth", "")
        category = item.get("category", "unknown")

        try:
            result = query_api(base_url, question, timeout)
            answer = result.get("answer", "")
            citations = result.get("citations", [])
            confidence = float(result.get("confidence", 0.0))
            escalated = bool(result.get("escalated", False))
            overlap = token_overlap(answer, ground_truth)
            has_citations = len(citations) > 0
        except Exception as exc:
            answer = ""
            citations = []
            confidence = 0.0
            escalated = True
            overlap = 0.0
            has_citations = False
            result = {"error": str(exc)}

        rows.append(
            {
                "question": question,
                "category": category,
                "answer": answer,
                "ground_truth": ground_truth,
                "token_overlap": round(overlap, 3),
                "has_citations": has_citations,
                "confidence": confidence,
                "escalated": escalated,
                "citation_count": len(citations),
                "raw": result,
            }
        )

    if not rows:
        return {"metrics": {}, "rows": []}

    metrics = {
        "samples": len(rows),
        "citation_rate": round(sum(1 for row in rows if row["has_citations"]) / len(rows), 3),
        "avg_token_overlap": round(sum(row["token_overlap"] for row in rows) / len(rows), 3),
        "avg_confidence": round(sum(row["confidence"] for row in rows) / len(rows), 3),
        "escalation_rate": round(sum(1 for row in rows if row["escalated"]) / len(rows), 3),
    }
    return {"metrics": metrics, "rows": rows}


def run_ragas_metrics(rows: list[dict]) -> dict | None:
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, context_precision, faithfulness
    except ModuleNotFoundError:
        return None

    contexts = []
    for row in rows:
        raw = row.get("raw", {})
        citations = raw.get("citations", []) if isinstance(raw, dict) else []
        contexts.append(
            [citation.get("chunk_text", "") for citation in citations if citation.get("chunk_text")]
        )

    dataset = Dataset.from_dict(
        {
            "question": [row["question"] for row in rows],
            "answer": [row["answer"] for row in rows],
            "contexts": contexts,
            "ground_truth": [row["ground_truth"] for row in rows],
        }
    )

    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
    )
    return {key: round(float(value), 3) for key, value in result.items()}


def print_markdown_table(metrics: dict) -> None:
    print("\n| Metric | Value |")
    print("|--------|-------|")
    for key, value in metrics.items():
        print(f"| {key} | {value} |")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run golden-set evaluation against query API")
    parser.add_argument(
        "--dataset",
        default=str(Path(__file__).with_name("golden_qa.json")),
        help="Path to golden QA JSON",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("EVAL_API_URL", "http://localhost:8000"),
        help="Backend base URL",
    )
    parser.add_argument("--timeout", type=float, default=90.0, help="Per-query timeout seconds")
    parser.add_argument("--limit", type=int, default=None, help="Optional question limit")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).with_name("ragas_results.json")),
        help="Where to write JSON results",
    )
    args = parser.parse_args()

    golden_set = load_golden_set(Path(args.dataset))
    print(f"Loaded {len(golden_set)} golden questions")

    baseline = run_baseline_metrics(args.api_url, golden_set, args.timeout, args.limit)
    metrics = {"baseline": baseline["metrics"]}

    ragas_metrics = run_ragas_metrics(baseline["rows"])
    if ragas_metrics:
        metrics["ragas"] = ragas_metrics
        print("\nRAGAS metrics:")
        print_markdown_table(ragas_metrics)
    else:
        print("\nRAGAS not installed; baseline metrics only.")
        print("Install with: pip install ragas datasets")

    print("\nBaseline metrics:")
    print_markdown_table(baseline["metrics"])

    output_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_url": args.api_url,
        "metrics": metrics,
        "rows": baseline["rows"],
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(output_payload, handle, indent=2)

    print(f"\nWrote results to {output_path}")


if __name__ == "__main__":
    main()
