from pathlib import Path

import pandas as pd


DATASET = Path("data/secondary_data.csv")


def main():
    df = pd.read_csv(DATASET, sep=";")

    print("=" * 60)
    print("DATASET SHAPE")
    print("=" * 60)
    print(df.shape)

    print("\n" + "=" * 60)
    print("COLUMNS")
    print("=" * 60)

    for i, column in enumerate(df.columns, start=1):
        print(f"{i:2}. {column}")

    print("\n" + "=" * 60)
    print("DATA TYPES")
    print("=" * 60)
    print(df.dtypes)

    print("\n" + "=" * 60)
    print("MISSING VALUES")
    print("=" * 60)
    print(df.isna().sum())

    print("\n" + "=" * 60)
    print("FIRST 5 ROWS")
    print("=" * 60)
    print(df.head().to_string())

    print("\n" + "=" * 60)
    print("UNIQUE VALUES PER COLUMN")
    print("=" * 60)

    for column in df.columns:
        print(f"\n{column}: {df[column].nunique()} unique values")
        print(df[column].unique()[:20])


if __name__ == "__main__":
    main()
