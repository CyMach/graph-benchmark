from pathlib import Path
import pandas as pd

SOURCE = Path("/Users/prabhukiranpagolu/Downloads/archive/secondary_data.csv")
OUTPUT = Path("data/benchmark/benchmark_dataset.csv")

N_ROWS = 30_000
SEED = 42

# These are the categorical attributes represented as graph relationships.
CATEGORICAL_COLUMNS = [
    "cap-shape",
    "cap-surface",
    "cap-color",
    "does-bruise-or-bleed",
    "gill-attachment",
    "gill-spacing",
    "gill-color",
    "stem-root",
    "stem-surface",
    "stem-color",
    "veil-type",
    "veil-color",
    "has-ring",
    "ring-type",
    "spore-print-color",
    "habitat",
    "season",
]


def main():
    print("=" * 70)
    print("PREPARING BENCHMARK DATASET")
    print("=" * 70)

    if not SOURCE.exists():
        raise FileNotFoundError(f"Source dataset not found: {SOURCE}")

    df = pd.read_csv(SOURCE, sep=";")

    print(f"Source rows: {len(df):,}")
    print(f"Source columns: {len(df.columns)}")

    if len(df) < N_ROWS:
        raise ValueError(
            f"Dataset has only {len(df)} rows; cannot sample {N_ROWS}."
        )

    # Deterministic random sample.
    benchmark = (
        df.sample(n=N_ROWS, random_state=SEED)
        .sort_index()
        .reset_index(drop=True)
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    benchmark.to_csv(OUTPUT, index=False, sep=";")

    # ------------------------------------------------------------
    # Calculate graph size using the same modeling assumption
    # used by our Neo4j graph:
    #
    #   one Mushroom node per row
    #   one value node per distinct categorical value
    #   one relationship for each non-null categorical attribute
    # ------------------------------------------------------------

    mushroom_nodes = len(benchmark)

    relationship_counts = {}
    value_node_counts = {}

    for column in CATEGORICAL_COLUMNS:
        non_null = benchmark[column].notna()

        relationship_counts[column] = int(non_null.sum())
        value_node_counts[column] = int(benchmark.loc[non_null, column].nunique())

    total_relationships = sum(relationship_counts.values())
    total_value_nodes = sum(value_node_counts.values())
    total_nodes = mushroom_nodes + total_value_nodes

    print()
    print("=" * 70)
    print("BENCHMARK DATASET")
    print("=" * 70)

    print(f"Rows:              {len(benchmark):,}")
    print(f"Columns:           {len(benchmark.columns)}")
    print(f"Random seed:       {SEED}")
    print(f"Output:            {OUTPUT}")

    print()
    print("RELATIONSHIPS")
    print("-" * 70)

    for column in CATEGORICAL_COLUMNS:
        print(
            f"{column:25s} "
            f"{relationship_counts[column]:>8,} relationships"
        )

    print()
    print("VALUE NODES")
    print("-" * 70)

    for column in CATEGORICAL_COLUMNS:
        print(
            f"{column:25s} "
            f"{value_node_counts[column]:>8,} values"
        )

    print()
    print("=" * 70)
    print("GRAPH SIZE")
    print("=" * 70)

    print(f"Mushroom nodes:       {mushroom_nodes:,}")
    print(f"Attribute value nodes:{total_value_nodes:,}")
    print(f"TOTAL NODES:          {total_nodes:,}")
    print(f"TOTAL RELATIONSHIPS:  {total_relationships:,}")

    print()
    print("=" * 70)
    print("DATASET READY")
    print("=" * 70)


if __name__ == "__main__":
    main()
