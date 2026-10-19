"""Execute a small authored retrieval set and controlled support-guard probes."""

import importlib.metadata
import json
import platform
import sqlite3
import statistics
import tempfile
import time
from pathlib import Path
from .engine import answer, connect, digest, ingest, retrieve
from .guard import triage


def guard_cases():
    evidence = "The local workflow requires approval before publication."
    return [
        ("exact_control", evidence, [evidence], False),
        ("missing_citation", evidence, [], True),
        (
            "unmatched_number",
            "There are 20000 observations.",
            ["There are 17379 observations."],
            True,
        ),
        ("unrelated", "Satellites measure ocean currents.", [evidence], True),
        (
            "negation_miss",
            "The local workflow does not require approval before publication.",
            [evidence],
            True,
        ),
        (
            "meaning_miss",
            "The local workflow guarantees complete factual correctness.",
            ["The local workflow cannot guarantee complete factual correctness."],
            True,
        ),
    ]


def main():
    raw = Path("queries.json").read_bytes()
    queries = json.loads(raw)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "evaluation.sqlite"
        ingestion = ingest("knowledge", path)
        results, all_times = {}, []
        with connect(path) as db:
            for method in ("bm25", "character", "hybrid"):
                records = []
                for item in queries:
                    started = time.perf_counter()
                    hits = retrieve(db, item["query"], 3, method)
                    seconds = time.perf_counter() - started
                    all_times.append(seconds)
                    rank = next(
                        (
                            i
                            for i, h in enumerate(hits, 1)
                            if h["document"] == item["expected_file"]
                        ),
                        None,
                    )
                    records.append(
                        {
                            **item,
                            "expected_file_rank": rank,
                            "retrieved_files": [h["document"] for h in hits],
                            "seconds": seconds,
                        }
                    )
                results[method] = {
                    "expected_file_hit_at_3_chunks": sum(
                        r["expected_file_rank"] is not None for r in records
                    )
                    / len(records),
                    "mrr_at_3_chunks": sum(
                        1 / r["expected_file_rank"] if r["expected_file_rank"] else 0
                        for r in records
                    )
                    / len(records),
                    "queries": records,
                }
            outputs = [answer(db, q["query"]) for q in queries]
            claims = [c for a in outputs for c in a["claims"]]
            exact = sum(c["text"] in c["citations"][0]["text"] for c in claims)
            chunk_count = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        cases = []
        for name, claim, sources, unsupported in guard_cases():
            score = triage(claim, [{"text": t} for t in sources])
            cases.append(
                {
                    "case": name,
                    "unsupported": unsupported,
                    "claim": claim,
                    "sources": sources,
                    **score,
                }
            )
        positives = [c for c in cases if c["unsupported"]]
        controls = [c for c in cases if not c["unsupported"]]
        report = {
            "scope": "Authored documentation queries and designed lexical-guard probes; no learned generation or independent relevance labels.",
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "versions": {
                p: importlib.metadata.version(p)
                for p in ("scikit-learn", "numpy", "scipy")
            },
            "query_sha256": digest(raw),
            "corpus_sha256": ingestion["corpus_sha256"],
            "documents": ingestion["documents"],
            "chunks": chunk_count,
            "queries": len(queries),
            "retrieval": results,
            "extractive": {
                "answered": sum(not a["abstained"] for a in outputs),
                "claims": len(claims),
                "exact_cited_spans": exact,
                "outputs": outputs,
                "limit": "Span identity is true by construction and is not a factual-faithfulness benchmark.",
            },
            "guard": {
                "unsupported": len(positives),
                "flagged_unsupported": sum(c["review_required"] for c in positives),
                "recall": sum(c["review_required"] for c in positives) / len(positives),
                "control_false_alarms": sum(c["review_required"] for c in controls),
                "controls": len(controls),
                "cases": cases,
            },
            "latency_seconds": {
                "median_retrieval": statistics.median(all_times),
                "p95_retrieval": sorted(all_times)[int(0.95 * (len(all_times) - 1))],
                "scope": "Local in-process retrieval including vectorizer refit; excludes dependency installation and HTTP transport.",
            },
            "billed_model_api_cost_usd": 0,
            "cpu_cost_usd": None,
            "limits": [
                "One small owner-authored corpus and 14 owner-authored queries, not external validation.",
                "One expected file per query; other retrieved files may also be relevant.",
                "Character TF-IDF is lexical matching, not semantic vector retrieval.",
                "RRF is an established algorithm and need not outperform the best individual baseline.",
                "The guard misses negation/semantic changes despite high token overlap.",
                "No paid model, free-form answer quality, production throughput or model-level prompt-injection result.",
            ],
        }
    Path("results").mkdir(exist_ok=True)
    Path("results/evaluation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k in ("documents", "chunks", "queries", "latency_seconds")
            },
            indent=2,
        )
    )
    print(
        json.dumps(
            {
                m: {k: v for k, v in r.items() if k != "queries"}
                for m, r in results.items()
            },
            indent=2,
        )
    )
    print("Guard recall:", report["guard"]["recall"])


if __name__ == "__main__":
    main()
