import argparse
import json
import random
import time
from pathlib import Path

from benchmark.workloads import WORKLOADS


RANDOM_SEED = 42
DEFAULT_WARMUP_RUNS = 10
DEFAULT_MEASURED_RUNS = 120


def percentile(values, p):
    values = sorted(values)

    if not values:
        return 0.0

    position = (len(values) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)

    if lower == upper:
        return values[lower]

    fraction = position - lower

    return (
        values[lower]
        + (values[upper] - values[lower]) * fraction
    )


def get_start_node_ids(db, count):
    result = db.execute(
        """
        MATCH (m:Mushroom)
        RETURN m.id AS id
        ORDER BY m.id
        """
    )

    ids = [record["id"] for record in result.records]

    if len(ids) < count:
        raise RuntimeError(
            f"Need {count} Mushroom IDs, found {len(ids)}"
        )

    rng = random.Random(RANDOM_SEED)

    return rng.sample(ids, count)


def get_habitats(db):
    result = db.execute(
        """
        MATCH (h:Habitat)
        RETURN h.value AS value
        ORDER BY h.value
        """
    )

    return [
        record["value"]
        for record in result.records
    ]


def make_parameters(
    workload,
    start_id,
    habitats,
    iteration,
):
    if workload.parameter_kind == "mushroom_id":
        return {
            "id": start_id,
        }

    if workload.parameter_kind == "mushroom_id_write":
        return {
            "id": start_id,
            "value": iteration,
        }

    if workload.parameter_kind == "habitat":
        return {
            "value": habitats[
                iteration % len(habitats)
            ],
        }

    return {}


def run_query(db, workload, parameters):
    result = db.execute(
        workload.query,
        **parameters,
    )

    # Force complete result consumption.
    list(result.records)


def benchmark_workload(
    db,
    workload,
    start_ids,
    habitats,
    warmup_runs,
    measured_runs,
):
    print(f"\n=== {workload.name} ===")

    total_runs = warmup_runs + measured_runs

    measurements = []

    for i in range(total_runs):
        start_id = start_ids[
            i % len(start_ids)
        ]

        parameters = make_parameters(
            workload,
            start_id,
            habitats,
            i,
        )

        start = time.perf_counter()

        run_query(
            db,
            workload,
            parameters,
        )

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        if i < warmup_runs:
            print(
                f"  warmup "
                f"{i + 1:02d}/{warmup_runs}: "
                f"{elapsed:.3f} ms"
            )
        else:
            measurements.append(elapsed)

            measured_index = (
                i - warmup_runs + 1
            )

            print(
                f"  run "
                f"{measured_index:03d}/"
                f"{measured_runs}: "
                f"{elapsed:.3f} ms"
            )

    mean_ms = (
        sum(measurements)
        / len(measurements)
    )

    p50_ms = percentile(
        measurements,
        0.50,
    )

    p95_ms = percentile(
        measurements,
        0.95,
    )

    p99_ms = percentile(
        measurements,
        0.99,
    )

    result = {
        "count": measured_runs,
        "warmup_runs": warmup_runs,
        "mean_ms": mean_ms,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "p99_ms": p99_ms,
        "min_ms": min(measurements),
        "max_ms": max(measurements),
        "throughput_qps": (
            1000.0 / mean_ms
        ),
        "workload": workload.name,
        "random_seed": RANDOM_SEED,
        "parameter_kind": workload.parameter_kind,
    }

    print(
        f"  p50: {p50_ms:.3f} ms | "
        f"p95: {p95_ms:.3f} ms | "
        f"p99: {p99_ms:.3f} ms | "
        f"QPS: {result['throughput_qps']:.2f}"
    )

    return result


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--platform",
        required=True,
        choices=[
            "neo4j",
            "cognodb",
        ],
    )

    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_MEASURED_RUNS,
    )

    parser.add_argument(
        "--warmup",
        type=int,
        default=DEFAULT_WARMUP_RUNS,
    )

    args = parser.parse_args()

    if args.runs < 1:
        raise ValueError(
            "--runs must be >= 1"
        )

    if args.warmup < 0:
        raise ValueError(
            "--warmup must be >= 0"
        )

    if args.platform == "neo4j":
        from benchmark.platforms.neo4j import (
            Neo4jAdapter,
        )

        db = Neo4jAdapter()

        output = Path(
            "results/raw/"
            "neo4j_standard_results.json"
        )

    else:
        from benchmark.platforms.cognodb import (
            CognoDBAdapter,
        )

        db = CognoDBAdapter()

        output = Path(
            "results/raw/"
            "cognodb_standard_results.json"
        )

    print(
        f"Platform: {args.platform}"
    )

    print(
        f"Warmup runs: {args.warmup}"
    )

    print(
        f"Measured runs: {args.runs}"
    )

    print(
        f"Random seed: {RANDOM_SEED}"
    )

    db.connect()

    try:
        required_ids = (
            args.warmup
            + args.runs
        )

        start_ids = get_start_node_ids(
            db,
            required_ids,
        )

        habitats = get_habitats(db)

        print(
            f"Selected {len(start_ids)} "
            f"deterministic random Mushroom "
            f"start nodes."
        )

        print(
            f"Habitat values: {habitats}"
        )

        results = []

        for workload in WORKLOADS:
            result = benchmark_workload(
                db=db,
                workload=workload,
                start_ids=start_ids,
                habitats=habitats,
                warmup_runs=args.warmup,
                measured_runs=args.runs,
            )

            results.append(result)

    finally:
        db.close()

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            results,
            indent=2,
        )
    )

    print(
        f"\nResults written to: {output}"
    )


if __name__ == "__main__":
    main()
