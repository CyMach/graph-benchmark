from benchmark.platforms.neo4j import Neo4jAdapter


def main():
    db = Neo4jAdapter()

    try:
        db.connect()

        records, summary, keys = db.execute(
            """
            RETURN 1 AS result
            """
        )

        print("Query result:", records[0]["result"])
        print(
            "Database response time:",
            summary.result_available_after,
            "ms",
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
