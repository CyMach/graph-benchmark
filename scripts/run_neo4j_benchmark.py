import json
import time
from pathlib import Path

from benchmark.platforms.neo4j import Neo4jAdapter
from benchmark.workloads import WORKLOADS


WARMUP_RUNS = 10
MEASURED_RUNS = 120

OUTPUT = Path("results/raw/neo4j_results.json")


def run_query(db, workload):
    result = db.execute(
        workload.query,
        **workload.parameters,
    )

    # Force result consumption so the measured time includes
    # server response and result processing.
    list(result.records)


def percentile(values, percentile):
    values = sorted(values)

    if not values:
        return 0.0

    position = (len(values) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(values))

    if lower == upper:
        return values[lower]

    fraction = position - lower

    return (
        values[lower]
        + (values[upper] - values[lower]) * fraction
    )


def benchmark_workload(db, workload):
    print(f"\n=== {workload.name} ===")

    # Warm-up runs
    for _ in range(WARMUP_RUNS):
        run_query(db, workload)

    measurements = []

    # Measured runs
    for i in range(MEASURED_RUNS):
        start = time.perf_counter()

        run_query(db, workload)

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        measurements.append(elapsed)

        print(
            f"  run {i + 1:02d}/{MEASURED_RUNS}: "
            f"{elapsed:.3f} ms"
        )

    mean_ms = sum(measurements) / len(measurements)

    p50_ms = percentile(
        measurements,
        0.50,
    )

    p95_ms = percentile(
        measurements,
        0.95,
    )

    min_ms = min(measurements)
    max_ms = max(measurements)

    throughput_qps = 1000.0 / mean_ms

    print(
        f"  p50: {p50_ms:.3f} ms | "
        f"p95: {p95_ms:.3f} ms | "
        f"QPS: {throughput_qps:.2f}"
    )

    return {
        "count": MEASURED_RUNS,
        "mean_ms": mean_ms,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "min_ms": min_ms,
        "max_ms": max_ms,
        "throughput_qps": throughput_qps,
        "workload": workload.name,
    }


def main():
    db = Neo4jAdapter()

    try:
        db.connect()

        results = []

        for workload in WORKLOADS:
            result = benchmark_workload(
                db,
                workload,
            )

            results.append(result)

    finally:
        db.close()

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            results,
            indent=2,
        )
    )

    print(
        f"\nResults written to: {OUTPUT}"
    )


if __name__ == "__main__":
    main()
