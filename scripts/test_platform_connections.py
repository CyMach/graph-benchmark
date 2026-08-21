from benchmark.platforms.neo4j_aura import Neo4jAuraAdapter
from benchmark.platforms.memgraph import MemgraphAdapter
from benchmark.platforms.falkordb import FalkorDBAdapter
from benchmark.platforms.arangodb import ArangoDBAdapter


def test_cypher_platform(name, adapter_class):
    print(f"\n=== {name} ===")

    db = adapter_class()

    try:
        db.connect()

        result = db.execute(
            "RETURN 1 AS value"
        )

        if hasattr(result, "records"):
            records = list(result.records)
        elif isinstance(result, list):
            records = result
        else:
            records = []

        print(f"{name}: query successful.")
        print(f"{name}: rows returned = {len(records)}")

        if records:
            print(f"{name}: first result = {records[0]}")

        return True

    except Exception as exc:
        print(f"{name}: FAILED")
        print(f"{type(exc).__name__}: {exc}")
        return False

    finally:
        db.close()


def test_arango():
    print("\n=== ArangoGraph ===")

    db = ArangoDBAdapter()

    try:
        db.connect()

        result = db.execute(
            "RETURN 1 AS value"
        )

        print("ArangoGraph: query successful.")
        print(f"ArangoGraph: rows returned = {len(result)}")

        if result:
            print(
                f"ArangoGraph: first result = {result[0]}"
            )

        return True

    except Exception as exc:
        print("ArangoGraph: FAILED")
        print(f"{type(exc).__name__}: {exc}")
        return False

    finally:
        db.close()


def main():
    results = []

    results.append(
        test_cypher_platform(
            "Neo4j Aura",
            Neo4jAuraAdapter,
        )
    )

    results.append(
        test_cypher_platform(
            "Memgraph",
            MemgraphAdapter,
        )
    )

    results.append(
        test_cypher_platform(
            "FalkorDB",
            FalkorDBAdapter,
        )
    )

    results.append(
        test_arango()
    )

    print("\n" + "=" * 60)
    print("CONNECTION TEST SUMMARY")
    print("=" * 60)

    names = [
        "Neo4j Aura",
        "Memgraph",
        "FalkorDB",
        "ArangoGraph",
    ]

    for name, success in zip(names, results):
        print(
            f"{name:<15} "
            f"{'PASS' if success else 'FAIL'}"
        )

    if not all(results):
        raise SystemExit(1)

    print("\nAll platform connection tests passed.")


if __name__ == "__main__":
    main()
