import sys
import time

from benchmark.dataset import load_dataset, iter_mushrooms
from benchmark.platforms.arangodb import ArangoDBAdapter


BATCH_SIZE = 1000


RELATIONSHIP_COLUMNS = {
    "cap-shape": "HAS_CAP_SHAPE",
    "cap-surface": "HAS_CAP_SURFACE",
    "cap-color": "HAS_CAP_COLOR",
    "does-bruise-or-bleed": "HAS_BRUISE_STATUS",
    "gill-attachment": "HAS_GILL_ATTACHMENT",
    "gill-spacing": "HAS_GILL_SPACING",
    "gill-color": "HAS_GILL_COLOR",
    "stem-root": "HAS_STEM_ROOT",
    "stem-surface": "HAS_STEM_SURFACE",
    "stem-color": "HAS_STEM_COLOR",
    "veil-type": "HAS_VEIL_TYPE",
    "veil-color": "HAS_VEIL_COLOR",
    "has-ring": "HAS_RING",
    "ring-type": "HAS_RING_TYPE",
    "spore-print-color": "HAS_SPORE_COLOR",
    "habitat": "IN_HABITAT",
    "season": "IN_SEASON",
}


def ensure_collections(db):
    graph_name = "mushroom_benchmark"

    if not db.db.has_graph(graph_name):
        db.db.create_graph(
            graph_name,
            edge_definitions=[
                {
                    "edge_collection": "relationships",
                    "from_vertex_collections": ["mushrooms"],
                    "to_vertex_collections": ["attributes"],
                }
            ],
        )

    vertex_collections = [
        "mushrooms",
        "attributes",
    ]

    for name in vertex_collections:
        if not db.db.has_collection(name):
            db.db.create_collection(name)

    return db.db.graph(graph_name)


def clear_graph(db):
    for name in [
        "relationships",
        "mushrooms",
        "attributes",
    ]:
        if db.db.has_collection(name):
            db.db.collection(name).truncate()


def load_mushrooms(db, batch):
    docs = []

    for row in batch:
        properties = row["properties"]

        docs.append(
            {
                "_key": str(properties["id"]),
                "id": properties["id"],
                "class": properties["class"],
                "cap_diameter": properties["cap_diameter"],
                "stem_height": properties["stem_height"],
                "stem_width": properties["stem_width"],
            }
        )

    db.db.collection(
        "mushrooms"
    ).insert_many(
        docs,
        overwrite=True,
    )


def attribute_key(label, value):
    safe_value = str(value).replace(
        " ",
        "_",
    )

    return (
        f"{label.lower()}_"
        f"{safe_value}"
    )


def load_relationships(db, batch):
    edges = []
    attributes = {}

    for row in batch:
        mushroom_id = str(row["id"])

        for relationship in row["relationships"]:
            relationship_type = relationship["type"]
            value = relationship["value"]

            label = {
                v: k
                for k, v in RELATIONSHIP_COLUMNS.items()
            }.get(
                relationship_type,
                relationship_type,
            )

            key = attribute_key(
                label,
                value,
            )

            attributes[key] = {
                "_key": key,
                "type": relationship_type,
                "attribute": label,
                "value": value,
            }

            edges.append(
                {
                    "_from": (
                        f"mushrooms/"
                        f"{mushroom_id}"
                    ),
                    "_to": (
                        f"attributes/"
                        f"{key}"
                    ),
                    "relationship_type": (
                        relationship_type
                    ),
                    "attribute": label,
                }
            )

    if attributes:
        db.db.collection(
            "attributes"
        ).insert_many(
            list(attributes.values()),
            overwrite=True,
        )

    if edges:
        db.db.collection(
            "relationships"
        ).insert_many(
            edges,
            overwrite=False,
            overwrite_mode="ignore",
        )


def main():
    test_mode = "--test" in sys.argv

    df = load_dataset()

    if test_mode:
        df = df.head(10)
        print(
            "TEST MODE: loading first 10 rows."
        )
    else:
        print(
            f"FULL MODE: loading "
            f"{len(df):,} rows."
        )

    records = list(
        iter_mushrooms(df)
    )

    db = ArangoDBAdapter()

    try:
        db.connect()
        ensure_collections(db)
        clear_graph(db)

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
            time.perf_counter()
            - start
        )

        print(
            f"\nLoad time: "
            f"{elapsed:.3f} seconds"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
