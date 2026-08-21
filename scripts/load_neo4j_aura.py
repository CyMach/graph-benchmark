import sys
import time

from benchmark.dataset import load_dataset, iter_mushrooms
from benchmark.platforms.neo4j_aura import Neo4jAuraAdapter


BATCH_SIZE = 1000

RELATIONSHIP_LABELS = {
    "HAS_CAP_SHAPE": "CapShape",
    "HAS_CAP_SURFACE": "CapSurface",
    "HAS_CAP_COLOR": "CapColor",
    "HAS_BRUISE_STATUS": "BruiseStatus",
    "HAS_GILL_ATTACHMENT": "GillAttachment",
    "HAS_GILL_SPACING": "GillSpacing",
    "HAS_GILL_COLOR": "GillColor",
    "HAS_STEM_ROOT": "StemRoot",
    "HAS_STEM_SURFACE": "StemSurface",
    "HAS_STEM_COLOR": "StemColor",
    "HAS_VEIL_TYPE": "VeilType",
    "HAS_VEIL_COLOR": "VeilColor",
    "HAS_RING": "RingStatus",
    "HAS_RING_TYPE": "RingType",
    "HAS_SPORE_COLOR": "SporeColor",
    "IN_HABITAT": "Habitat",
    "IN_SEASON": "Season",
}


def create_schema(db):
    db.execute(
        """
        CREATE CONSTRAINT mushroom_id_unique IF NOT EXISTS
        FOR (m:Mushroom)
        REQUIRE m.id IS UNIQUE
        """
    )


def load_mushrooms(db, batch):
    db.execute(
        """
        UNWIND $rows AS row
        MERGE (m:Mushroom {id: row.properties.id})
        SET m.class = row.properties.class,
            m.cap_diameter = row.properties.cap_diameter,
            m.stem_height = row.properties.stem_height,
            m.stem_width = row.properties.stem_width
        """,
        rows=batch,
    )


def load_relationships(db, batch):
    for relationship_type, label in RELATIONSHIP_LABELS.items():
        rows = []

        for row in batch:
            for relationship in row["relationships"]:
                if relationship["type"] == relationship_type:
                    rows.append(
                        {
                            "mushroom_id": row["id"],
                            "value": relationship["value"],
                        }
                    )

        if not rows:
            continue

        query = f"""
        UNWIND $rows AS row
        MATCH (m:Mushroom {{id: row.mushroom_id}})
        MERGE (v:{label} {{value: row.value}})
        MERGE (m)-[:{relationship_type}]->(v)
        """

        db.execute(
            query,
            rows=rows,
        )


def main():
    test_mode = "--test" in sys.argv

    df = load_dataset()

    if test_mode:
        df = df.head(10)
        print("TEST MODE: loading first 10 rows.")
    else:
        print(
            f"FULL MODE: loading {len(df):,} rows."
        )

    records = list(iter_mushrooms(df))

    db = Neo4jAuraAdapter()

    try:
        db.connect()
        create_schema(db)

        start = time.perf_counter()

        for start_index in range(
            0,
            len(records),
            BATCH_SIZE,
        ):
            batch = records[
                start_index:start_index + BATCH_SIZE
            ]

            load_mushrooms(
                db,
                batch,
            )

            load_relationships(
                db,
                batch,
            )

            end_index = min(
                start_index + len(batch),
                len(records),
            )

            print(
                f"Loaded "
                f"{end_index:,}/"
                f"{len(records):,} mushrooms"
            )

        elapsed = (
            time.perf_counter() - start
        )

        print(
            f"\nLoad time: {elapsed:.3f} seconds"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
