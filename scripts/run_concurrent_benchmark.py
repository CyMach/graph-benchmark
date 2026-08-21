import argparse
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

RANDOM_SEED = 42

DEFAULT_WARMUP_SECONDS = 10
DEFAULT_MEASURE_SECONDS = 30

OUTPUT_DIR = Path("results/raw")

READ_QUERY = """
MATCH (m:Mushroom {id: $id})
RETURN m.id AS id,
       m.class AS class
"""

WRITE_QUERY = """
MATCH (m:Mushroom {id: $id})
SET m.benchmark_touch = $value
RETURN m.id AS id
"""


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


def create_adapter(platform):
    if platform == "neo4j":
        from benchmark.platforms.neo4j import Neo4jAdapter
        return Neo4jAdapter()

    if platform == "cognodb":
        from benchmark.platforms.cognodb import CognoDBAdapter
        return CognoDBAdapter()

    raise ValueError(f"Unknown platform: {platform}")


def get_mushroom_ids(db):
    result = db.execute(
        """
        MATCH (m:Mushroom)
        RETURN m.id AS id
        ORDER BY m.id
        """
    )

    ids = [record["id"] for record in result.records]

    if not ids:
        raise RuntimeError("No Mushroom nodes found.")

    return ids


def execute_one(
    db,
    mushroom_id,
    operation_number,
):
    start = time.perf_counter()

    try:
        # 80% reads, 20% writes.
        if operation_number % 5 == 0:
            result = db.execute(
                WRITE_QUERY,
                id=mushroom_id,
                value=operation_number,
            )

            list(result.records)

            operation_type = "write"

        else:
            result = db.execute(
                READ_QUERY,
                id=mushroom_id,
            )

            list(result.records)

            operation_type = "read"

        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        return {
            "type": operation_type,
            "success": True,
            "latency_ms": elapsed_ms,
            "error": None,
        }

    except Exception as exc:
        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        return {
            "type": "error",
            "success": False,
            "latency_ms": elapsed_ms,
            "error": repr(exc),
        }


def worker(
    platform,
    ids,
    warmup_seconds,
    measure_seconds,
    worker_id,
):
    """
    One persistent database connection per worker.

    This is critical: connection establishment is outside
    the measured query loop.
    """

    db = create_adapter(platform)

    try:
        db.connect()

        rng = random.Random(
            RANDOM_SEED + worker_id
        )

        # -----------------------------------------------------
        # Warm-up
        # -----------------------------------------------------

        warmup_end = (
            time.perf_counter()
            + warmup_seconds
        )

        operation_number = worker_id * 1_000_000

        while time.perf_counter() < warmup_end:
            mushroom_id = rng.choice(ids)

            execute_one(
                db,
                mushroom_id,
                operation_number,
            )

            operation_number += 1

        # -----------------------------------------------------
        # Measurement
        # -----------------------------------------------------

        measurement_end = (
            time.perf_counter()
            + measure_seconds
        )

        results = []

        while time.perf_counter() < measurement_end:
            mushroom_id = rng.choice(ids)

            result = execute_one(
                db,
                mushroom_id,
                operation_number,
            )

            results.append(result)

            operation_number += 1

        return results

    finally:
        db.close()


def run_concurrency_test(
    platform,
    concurrency,
    warmup_seconds,
    measure_seconds,
    ids,
):
    print(
        f"\n=== {platform} | "
        f"{concurrency} concurrent clients ==="
    )

    start = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:

        futures = [
            executor.submit(
                worker,
                platform,
                ids,
                warmup_seconds,
                measure_seconds,
                worker_id,
            )
            for worker_id in range(concurrency)
        ]

        all_results = []

        for future in as_completed(futures):
            all_results.extend(
                future.result()
            )

    actual_duration = (
        time.perf_counter() - start
    )

    # ---------------------------------------------------------
    # Aggregate
    # ---------------------------------------------------------

    successful = [
        r
        for r in all_results
        if r["success"]
    ]

    failed = [
        r
        for r in all_results
        if not r["success"]
    ]

    reads = [
        r
        for r in successful
        if r["type"] == "read"
    ]

    writes = [
        r
        for r in successful
        if r["type"] == "write"
    ]

    latencies = [
        r["latency_ms"]
        for r in successful
    ]

    read_latencies = [
        r["latency_ms"]
        for r in reads
    ]

    write_latencies = [
        r["latency_ms"]
        for r in writes
    ]

    successful_count = len(successful)
    failed_count = len(failed)

    result = {
        "platform": platform,
        "concurrency": concurrency,

        "warmup_seconds": warmup_seconds,
        "measure_seconds": measure_seconds,

        "random_seed": RANDOM_SEED,

        "total_operations": len(all_results),
        "successful_operations": successful_count,
        "failed_operations": failed_count,

        "read_operations": len(reads),
        "write_operations": len(writes),

        "overall_qps": (
            successful_count
            / actual_duration
        ),

        "read_qps": (
            len(reads)
            / actual_duration
        ),

        "write_qps": (
            len(writes)
            / actual_duration
        ),

        "p50_ms": percentile(
            latencies,
            0.50,
        ),

        "p95_ms": percentile(
            latencies,
            0.95,
        ),

        "p99_ms": percentile(
            latencies,
            0.99,
        ),

        "read_p50_ms": percentile(
            read_latencies,
            0.50,
        ),

        "read_p95_ms": percentile(
            read_latencies,
            0.95,
        ),

        "write_p50_ms": percentile(
            write_latencies,
            0.50,
        ),

        "write_p95_ms": percentile(
            write_latencies,
            0.95,
        ),
    }

    print(
        f"Operations: "
        f"{successful_count:,}"
    )

    print(
        f"Errors: "
        f"{failed_count:,}"
    )

    print(
        f"Reads: "
        f"{len(reads):,}"
    )

    print(
        f"Writes: "
        f"{len(writes):,}"
    )

    print(
        f"Overall QPS: "
        f"{result['overall_qps']:.2f}"
    )

    print(
        f"Read QPS: "
        f"{result['read_qps']:.2f}"
    )

    print(
        f"Write QPS: "
        f"{result['write_qps']:.2f}"
    )

    print(
        f"p50: "
        f"{result['p50_ms']:.3f} ms | "
        f"p95: "
        f"{result['p95_ms']:.3f} ms | "
        f"p99: "
        f"{result['p99_ms']:.3f} ms"
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
        "--concurrency",
        type=int,
        nargs="+",
        default=[10],
    )

    parser.add_argument(
        "--warmup",
        type=int,
        default=DEFAULT_WARMUP_SECONDS,
    )

    parser.add_argument(
        "--seconds",
        type=int,
        default=DEFAULT_MEASURE_SECONDS,
    )

    args = parser.parse_args()

    if args.warmup < 0:
        raise ValueError(
            "--warmup must be >= 0"
        )

    if args.seconds < 1:
        raise ValueError(
            "--seconds must be >= 1"
        )

    if any(
        value < 1
        for value in args.concurrency
    ):
        raise ValueError(
            "--concurrency values must be >= 1"
        )

    db = create_adapter(
        args.platform
    )

    try:
        db.connect()

        ids = get_mushroom_ids(db)

        print(
            f"Platform: {args.platform}"
        )

        print(
            f"Mushroom IDs available: "
            f"{len(ids):,}"
        )

    finally:
        db.close()

    all_results = []

    for concurrency in args.concurrency:
        result = run_concurrency_test(
            platform=args.platform,
            concurrency=concurrency,
            warmup_seconds=args.warmup,
            measure_seconds=args.seconds,
            ids=ids,
        )

        all_results.append(result)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = (
        OUTPUT_DIR
        / f"{args.platform}_concurrent_results.json"
    )

    output.write_text(
        json.dumps(
            all_results,
            indent=2,
        )
    )

    print(
        f"\nResults written to: {output}"
    )


if __name__ == "__main__":
    main()
