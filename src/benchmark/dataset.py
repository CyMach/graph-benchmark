from pathlib import Path

import pandas as pd


DATASET_PATH = Path("data/benchmark/benchmark_dataset.csv")


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


def load_dataset():
    return pd.read_csv(DATASET_PATH, sep=";")


def normalize_value(value):
    if pd.isna(value):
        return None

    return str(value)


def iter_mushrooms(df):
    for index, row in df.iterrows():
        mushroom_id = index + 1

        properties = {
            "id": mushroom_id,
            "class": row["class"],
            "cap_diameter": float(row["cap-diameter"]),
            "stem_height": float(row["stem-height"]),
            "stem_width": float(row["stem-width"]),
        }

        relationships = []

        for column, relationship_type in RELATIONSHIP_COLUMNS.items():
            value = normalize_value(row[column])

            if value is not None:
                relationships.append(
                    {
                        "type": relationship_type,
                        "attribute": column,
                        "value": value,
                    }
                )

        yield {
            "id": mushroom_id,
            "properties": properties,
            "relationships": relationships,
        }
