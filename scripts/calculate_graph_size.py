from pathlib import Path

import pandas as pd


DATASET = Path("data/secondary_data.csv")


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


def main():
    df = pd.read_csv(DATASET, sep=";")

    mushroom_count = len(df)

    print("=" * 70)
    print("CANONICAL GRAPH SIZE ESTIMATE")
    print("=" * 70)

    print(f"Mushroom nodes: {mushroom_count:,}")

    total_relationships = 0

    print("\nRelationships by type:")

    for column, relationship in RELATIONSHIP_COLUMNS.items():
        count = int(df[column].notna().sum())
        total_relationships += count

        print(
            f"{relationship:25} "
            f"{count:8,}"
        )

    # Unique categorical value nodes.
    value_nodes = 0

    print("\nCategorical value nodes:")

    for column in RELATIONSHIP_COLUMNS:
        count = int(df[column].dropna().nunique())
        value_nodes += count

        print(
            f"{column:25} "
            f"{count:8,}"
        )

    total_nodes = mushroom_count + value_nodes

    print("\n" + "=" * 70)
    print(f"Mushroom nodes:          {mushroom_count:,}")
    print(f"Attribute value nodes:   {value_nodes:,}")
    print(f"TOTAL NODES:             {total_nodes:,}")
    print(f"TOTAL RELATIONSHIPS:     {total_relationships:,}")
    print("=" * 70)


if __name__ == "__main__":
    main()
