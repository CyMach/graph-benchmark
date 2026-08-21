import argparse
import json
import random
import statistics
import threading
import time
from pathlib import Path


PLATFORMS = [
    "cognodb",
    "neo4j_aura",
    "memgraph",
    "falkordb",
    "arangodb",
]

RANDOM_SEED = 42
START_NODE_COUNT = 30_000

OUTPUT_DIR = Path("results/raw/final")


# ------------------------------------------------------------------
# Mixed workload
#
# 80% reads:
#   point lookup
#   1-hop habitat
#   2-hop shared stem root
#
# 20% writes:
#   benchmark_touch update
#
# The workload is intentionally simple and identical in logical
# behavior across platforms.
# ------------------------------------------------------------------

CYPHER_READ_QUERIES = [
    (
        "point_lookup",
        """
        MATCH (m:Mushroom {id: $mushroom_id})
        RETURN m.id AS id,
               m.class AS class,
               m.cap_diameter AS cap_diameter,
               m.stem_height AS stem_height,
               m.stem_width AS stem_width
        """,
    ),
    (
        "1_hop_habitat",
        """
        MATCH (m:Mushroom {id: $mushroom_id})
              -[:IN_HABITAT]->(h:Habitat)
        RETURN h.value AS value
        """,
    ),
    (
        "2_hop_shared_stem_root",
        """
        MATCH (m1:Mushroom {id: $mushroom_id})
              -[:HAS_STEM_ROOT]->(s:StemRoot)
              <-[:HAS_STEM_ROOT]-(m2:Mushroom)
        WHERE m2.id <> m1.id
        RETURN count(DISTINCT m2) AS count
        """,
    ),
]

CYPHER_WRITE_QUERY = """
    MATCH (m:Mushroom {id: $mushroom_id})
    SET m.benchmark_touch = $value
    RETURN m.id AS id
"""


ARANGO_READ_QUERIES = [
    (
        "point_lookup",
        """
        FOR m IN mushrooms
            FILTER m.id == @mushroom_id
            RETURN {
                id: m.id,
                class: m.class,
                cap_diameter: m.cap_diameter,
                stem_height: m.stem_height,
                stem_width: m.stem_width
            }
        """,
    ),
    (
        "1_hop_habitat",
        """
        FOR m IN mushrooms
            FILTER m.id == @mushroom_id

            FOR e IN relationships
                FILTER e._from == m._id
                FILTER e.relationship_type == "IN_HABITAT"

                FOR h IN attributes
                    FILTER h._id == e._to

                    RETURN h.value
        """,
    ),
    (
        "2_hop_shared_stem_root",
        """
        LET start_id = CONCAT(
            "mushrooms/",
            TO_STRING(@mushroom_id)
        )

        LET count = LENGTH(
            FOR e1 IN relationships
                FILTER e1._from == start_id
                FILTER e1.relationship_type == "HAS_STEM_ROOT"

                FOR e2 IN relationships
                    FILTER e2._to == e1._to
                    FILTER e2.relationship_type == "HAS_STEM_ROOT"
                    FILTER e2._from != start_id

                    RETURN DISTINCT e2._from
        )

        RETURN count
        """,
    ),
]

ARANGO_WRITE_QUERY = """
    FOR m IN mushrooms
        FILTER m.id == @mushroom_id

        UPDATE m WITH {
            benchmark_touch: @value
        } IN mushrooms

        RETURN NEW.id
"""


def create_adapter(platform):
    if platform == "cognodb":
        from benchmark.platforms.cognodb import CognoDBAdapter
        return CognoDBAdapter()

    if platform == "neo4j_aura":
        from benchmark.platforms.neo4j_aura import Neo4jAuraAdapter
        return Neo4jAuraAdapter()

    if platform == "memgraph":
        from benchmark.platforms.memgraph import MemgraphAdapter
        return MemgraphAdapter()

    if platform == "falkordb":
        from benchmark.platforms.falkordb import FalkorDBAdapter
        return FalkorDBAdapter()

    if platform == "arangodb":
        from benchmark.platforms.arangodb import ArangoDBAdapter
        return ArangoDBAdapter()

    raise ValueError(platform)


def execute_query(
    db,
    platform,
    query,
    parameters,
):
    if platform == "arangodb":
        arango_parameters = {
            key: value
            for key, value in parameters.items()
            if f"@{key}" in query
        }

        return db.execute(
            query,
            **arango_parameters,
        )

    result = db.execute(
        query,
        **parameters,
    )

    if hasattr(result, "records"):
        return list(result.records)

    if hasattr(result, "result_set"):
        return result.result_set

    if isinstance(result, list):
        return result

    return []


def choose_workload(
    rng,
    platform,
):
    if rng.random() < 0.20:
        if platform == "arangodb":
            return (
                "write",
                ARANGO_WRITE_QUERY,
            )

        return (
            "write",
            CYPHER_WRITE_QUERY,
        )

    if platform == "arangodb":
        name, query = rng.choice(
            ARANGO_READ_QUERIES
        )
    else:
        name, query = rng.choice(
            CYPHER_READ_QUERIES
        )

    return (
        name,
        query,
    )


def make_parameters(
    rng,
    operation_index,
):
    mushroom_id = rng.randint(
        1,
        START_NODE_COUNT,
    )

    return {
        "mushroom_id": mushroom_id,
        "value": operation_index,
    }


def percentile(values, p):
    if not values:
        return 0.0

    values = sorted(values)

    position = (len(values) - 1) * p
    lower = int(position)
    upper = min(
        lower + 1,
        len(values) - 1,
    )

    if lower == upper:
        return values[lower]

    fraction = position - lower

    return (
        values[lower]
        + (
            values[upper]
            - values[lower]
        ) * fraction
    )


def worker(
    platform,
    stop_event,
    results,
    worker_id,
):
    db = create_adapter(platform)

    rng = random.Random(
        RANDOM_SEED + worker_id
    )

    local_index = 0

    try:
        db.connect()

        while not stop_event.is_set():
            operation_name, query = choose_workload(
                rng,
                platform,
            )

            parameters = make_parameters(
                rng,
                local_index,
            )

            start = time.perf_counter()

            try:
                execute_query(
                    db,
                    platform,
                    query,
                    parameters,
                )

                elapsed_ms = (
                    time.perf_counter()
                    - start
                ) * 1000

                results.append(
                    {
                        "success": True,
                        "operation": operation_name,
                        "elapsed_ms": elapsed_ms,
                        "is_write": (
                            operation_name == "write"
                        ),
                    }
                )

            except Exception as exc:
                elapsed_ms = (
                    time.perf_counter()
                    - start
                ) * 1000

                results.append(
                    {
                        "success": False,
                        "operation": operation_name,
                        "elapsed_ms": elapsed_ms,
                        "is_write": (
                            operation_name == "write"
                        ),
                        "error": (
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                    }
                )

            local_index += 1

    finally:
        db.close()


def run_trial(
    platform,
    concurrency,
    warmup_seconds,
    measure_seconds,
):
    print(
        f"\n=== {platform} | "
        f"{concurrency} concurrent clients ==="
    )

    # --------------------------------------------------------------
    # Warm-up
    # --------------------------------------------------------------
    stop_event = threading.Event()
    warmup_results = []

    workers = []

    for worker_id in range(concurrency):
        thread = threading.Thread(
            target=worker,
            args=(
                platform,
                stop_event,
                warmup_results,
                worker_id,
            ),
            daemon=True,
        )
        workers.append(thread)
        thread.start()

    print(
        f"Warm-up: {warmup_seconds} seconds"
    )

    time.sleep(warmup_seconds)

    stop_event.set()

    for thread in workers:
        thread.join()

    print(
        f"Warm-up operations: "
        f"{len(warmup_results)}"
    )

    # --------------------------------------------------------------
    # Measurement
    # --------------------------------------------------------------
    stop_event = threading.Event()
    results = []

    workers = []

    for worker_id in range(concurrency):
        thread = threading.Thread(
            target=worker,
            args=(
                platform,
                stop_event,
                results,
                worker_id + 1000,
            ),
            daemon=True,
        )
        workers.append(thread)
        thread.start()

    print(
        f"Measurement: {measure_seconds} seconds"
    )

    time.sleep(measure_seconds)

    stop_event.set()

    for thread in workers:
        thread.join()

    successful = [
        result
        for result in results
        if result["success"]
    ]

    failed = [
        result
        for result in results
        if not result["success"]
    ]

    read_results = [
        result
        for result in successful
        if not result["is_write"]
    ]

    write_results = [
        result
        for result in successful
        if result["is_write"]
    ]

    measured_count = len(results)

    overall_qps = (
        measured_count
        / measure_seconds
    )

    read_qps = (
        len(read_results)
        / measure_seconds
    )

    write_qps = (
        len(write_results)
        / measure_seconds
    )

    all_latencies = [
        result["elapsed_ms"]
        for result in successful
    ]

    read_latencies = [
        result["elapsed_ms"]
        for result in read_results
    ]

    write_latencies = [
        result["elapsed_ms"]
        for result in write_results
    ]

    record = {
        "platform": platform,
        "concurrency": concurrency,
        "warmup_seconds": warmup_seconds,
        "measure_seconds": measure_seconds,
        "random_seed": RANDOM_SEED,
        "total_operations": measured_count,
        "successful_operations": len(successful),
        "failed_operations": len(failed),
        "read_operations": len(read_results),
        "write_operations": len(write_results),
        "overall_qps": overall_qps,
        "read_qps": read_qps,
        "write_qps": write_qps,
        "p50_ms": percentile(
            all_latencies,
            0.50,
        ),
        "p95_ms": percentile(
            all_latencies,
            0.95,
        ),
        "p99_ms": percentile(
            all_latencies,
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
        f"Operations: {measured_count:,}"
    )

    print(
        f"Errors: {len(failed):,}"
    )

    print(
        f"Reads: {len(read_results):,}"
    )

    print(
        f"Writes: {len(write_results):,}"
    )

    print(
        f"Overall QPS: {overall_qps:.2f}"
    )

    print(
        f"Read QPS: {read_qps:.2f}"
    )

    print(
        f"Write QPS: {write_qps:.2f}"
    )

    print(
        f"p50: {record['p50_ms']:.3f} ms | "
        f"p95: {record['p95_ms']:.3f} ms | "
        f"p99: {record['p99_ms']:.3f} ms"
    )

    return record


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--platform",
        required=True,
        choices=PLATFORMS,
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        nargs="+",
        default=[1, 2, 4, 8, 16, 40],
    )

    parser.add_argument(
        "--warmup",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--seconds",
        type=int,
        default=30,
    )

    args = parser.parse_args()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_results = []

    for concurrency in args.concurrency:
        if concurrency < 1:
            raise ValueError(
                "--concurrency values must be >= 1"
            )

        record = run_trial(
            platform=args.platform,
            concurrency=concurrency,
            warmup_seconds=args.warmup,
            measure_seconds=args.seconds,
        )

        all_results.append(record)

    output = (
        OUTPUT_DIR
        / f"{args.platform}_concurrent_"
        f"results.json"
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
