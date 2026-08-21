import argparse
import json
import random
import time
from pathlib import Path


PLATFORM_NAMES = [
    "cognodb",
    "neo4j_aura",
    "memgraph",
    "falkordb",
    "arangodb",
]

RANDOM_SEED = 42

DEFAULT_WARMUP_RUNS = 10
DEFAULT_MEASURED_RUNS = 120

DATASET_SIZE = 30_000

OUTPUT_DIR = Path("results/raw/final")


# Deterministic start-node pool.
# The same IDs are used on every platform.
rng = random.Random(RANDOM_SEED)
START_IDS = rng.sample(
    range(1, DATASET_SIZE + 1),
    5,
)

# The same habitat values are cycled across platforms.
HABITATS = [
    "d",
    "g",
    "h",
    "l",
    "m",
    "p",
    "u",
    "w",
]


# ------------------------------------------------------------------
# Cypher workloads
#
# Used by:
#   CognoDB
#   Neo4j Aura
#   Memgraph
#   FalkorDB
# ------------------------------------------------------------------

CYPHER_WORKLOADS = {
    "1_hop_habitat": """
        MATCH (m:Mushroom {id: $mushroom_id})
              -[:IN_HABITAT]->(h:Habitat)
        RETURN h.value AS value
    """,

    "2_hop_shared_stem_root": """
        MATCH (m1:Mushroom {id: $mushroom_id})
              -[:HAS_STEM_ROOT]->(s:StemRoot)
              <-[:HAS_STEM_ROOT]-(m2:Mushroom)
        WHERE m2.id <> m1.id
        RETURN count(DISTINCT m2) AS count
    """,

    "3_hop_stem_root_season": """
        MATCH (m:Mushroom {id: $mushroom_id})
              -[:HAS_STEM_ROOT]->(s:StemRoot)
              <-[:HAS_STEM_ROOT]-(m2:Mushroom)
              -[:IN_SEASON]->(season:Season)
        WHERE m2.id <> m.id
        RETURN count(DISTINCT season) AS count
    """,

    "point_lookup": """
        MATCH (m:Mushroom {id: $mushroom_id})
        RETURN m.id AS id,
               m.class AS class,
               m.cap_diameter AS cap_diameter,
               m.stem_height AS stem_height,
               m.stem_width AS stem_width
    """,

    "indexed_habitat_lookup": """
        MATCH (h:Habitat {value: $habitat})
        MATCH (m:Mushroom)-[:IN_HABITAT]->(h)
        RETURN count(m) AS count
    """,

    "aggregation": """
        MATCH (m:Mushroom)
        RETURN m.class AS class,
               count(m) AS count
        ORDER BY class
    """,

    "mixed_read_write": """
        MATCH (m:Mushroom {id: $mushroom_id})
        SET m.benchmark_touch = $value
        RETURN m.id AS id
    """,
}


# ------------------------------------------------------------------
# ArangoDB AQL equivalents
#
# ArangoDB stores:
#   mushrooms       -> vertex documents
#   attributes      -> vertex documents
#   relationships   -> edge documents
# ------------------------------------------------------------------

ARANGO_WORKLOADS = {
    "1_hop_habitat": """
        FOR m IN mushrooms
            FILTER m.id == @mushroom_id

            FOR e IN relationships
                FILTER e._from == m._id
                FILTER e.relationship_type == "IN_HABITAT"

                FOR h IN attributes
                    FILTER h._id == e._to

                    RETURN h.value
    """,

    "2_hop_shared_stem_root": """
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

    "3_hop_stem_root_season": """
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

                    FOR e3 IN relationships
                        FILTER e3._from == e2._from
                        FILTER e3.relationship_type == "IN_SEASON"

                        RETURN DISTINCT e3._to
        )

        RETURN count
    """,

    "point_lookup": """
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

    "indexed_habitat_lookup": """
        FOR h IN attributes
            FILTER h.type == "IN_HABITAT"
            FILTER h.value == @habitat

            FOR e IN relationships
                FILTER e._to == h._id
                FILTER e.relationship_type == "IN_HABITAT"

                COLLECT WITH COUNT INTO count

                RETURN count
    """,

    "aggregation": """
        FOR m IN mushrooms
            COLLECT class = m.class
            WITH COUNT INTO count

            SORT class

            RETURN {
                class: class,
                count: count
            }
    """,

    "mixed_read_write": """
        FOR m IN mushrooms
            FILTER m.id == @mushroom_id

            UPDATE m WITH {
                benchmark_touch: @value
            } IN mushrooms

            RETURN NEW.id
    """,
}


def percentile(values, p):
    ordered = sorted(values)

    if not ordered:
        return 0.0

    position = (len(ordered) - 1) * p
    lower = int(position)
    upper = min(
        lower + 1,
        len(ordered) - 1,
    )

    if lower == upper:
        return ordered[lower]

    fraction = position - lower

    return (
        ordered[lower]
        + (
            ordered[upper]
            - ordered[lower]
        ) * fraction
    )


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

    raise ValueError(
        f"Unsupported platform: {platform}"
    )


def get_workloads(platform):
    if platform == "arangodb":
        return ARANGO_WORKLOADS

    return CYPHER_WORKLOADS


def make_parameters(
    workload_name,
    iteration,
):
    start_id = START_IDS[
        iteration % len(START_IDS)
    ]

    habitat = HABITATS[
        iteration % len(HABITATS)
    ]

    return {
        "mushroom_id": start_id,
        "habitat": habitat,
        "value": iteration,
    }


def execute_query(
    db,
    platform,
    query,
    parameters,
):
    if platform == "arangodb":
        # ArangoDB rejects bind variables that are
        # supplied but not used by the AQL query.
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


def benchmark_workload(
    db,
    platform,
    workload_name,
    query,
    warmup_runs,
    measured_runs,
):
    print(
        f"\n=== {workload_name} ==="
    )

    # --------------------------------------------------------------
    # Warm-up
    # --------------------------------------------------------------
    for i in range(warmup_runs):
        parameters = make_parameters(
            workload_name,
            i,
        )

        execute_query(
            db,
            platform,
            query,
            parameters,
        )

        print(
            f"  warmup "
            f"{i + 1:02d}/"
            f"{warmup_runs}"
        )

    # --------------------------------------------------------------
    # Measured runs
    # --------------------------------------------------------------
    measurements = []

    for i in range(measured_runs):
        parameters = make_parameters(
            workload_name,
            warmup_runs + i,
        )

        start = time.perf_counter()

        records = execute_query(
            db,
            platform,
            query,
            parameters,
        )

        elapsed_ms = (
            time.perf_counter()
            - start
        ) * 1000

        measurements.append(
            elapsed_ms
        )

        print(
            f"  run "
            f"{i + 1:03d}/"
            f"{measured_runs}: "
            f"{elapsed_ms:.3f} ms "
            f"rows={len(records)}"
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

    min_ms = min(measurements)
    max_ms = max(measurements)

    throughput_qps = (
        1000.0 / mean_ms
    )

    result = {
        "platform": platform,
        "workload": workload_name,
        "count": measured_runs,
        "warmup_runs": warmup_runs,
        "random_seed": RANDOM_SEED,
        "start_node_ids": START_IDS,
        "habitat_values": HABITATS,
        "mean_ms": mean_ms,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "p99_ms": p99_ms,
        "min_ms": min_ms,
        "max_ms": max_ms,
        "throughput_qps": throughput_qps,
    }

    print(
        f"  p50: {p50_ms:.3f} ms | "
        f"p95: {p95_ms:.3f} ms | "
        f"p99: {p99_ms:.3f} ms | "
        f"QPS: {throughput_qps:.2f}"
    )

    return result


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--platform",
        required=True,
        choices=PLATFORM_NAMES,
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

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = (
        OUTPUT_DIR
        / f"{args.platform}_standard_"
        f"{args.runs}runs.json"
    )

    db = create_adapter(
        args.platform
    )

    results = []

    try:
        db.connect()

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
        print(
            f"Start node IDs: {START_IDS}"
        )
        print(
            f"Habitat values: {HABITATS}"
        )

        workloads = get_workloads(
            args.platform
        )

        for name, query in workloads.items():
            result = benchmark_workload(
                db=db,
                platform=args.platform,
                workload_name=name,
                query=query,
                warmup_runs=args.warmup,
                measured_runs=args.runs,
            )

            results.append(result)

    finally:
        db.close()

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
