"""Step 1 - Clean the raw data with the five rules frozen in Week 3.

Rules (in order):
  1. Remove rows with a missing CustomerID.
  2. Remove exact duplicate rows.
  3. Remove cancellations (InvoiceNo starting with 'C').
  4. Remove non-positive unit prices.
  5. Remove administrative stock codes: POST, M, C2, DOT, BANK CHARGES
     (postage, manual entries, carriage, bank fees - not real products).
     PADS is a real product and is kept.

Week 3 reference numbers: 391,153 invoice lines / 4,334 customers / 18,402 invoices.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "online_retail_raw.csv"
OUT = ROOT / "data" / "processed" / "retail_clean.csv"

ADMIN_CODES = {"POST", "M", "C2", "DOT", "BANK CHARGES"}


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(
        RAW_CSV,
        dtype={"InvoiceNo": str, "StockCode": str},
        parse_dates=["InvoiceDate"],
    )
    return df


def clean(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    steps = []

    def log(rule: str, before: int, after: int):
        steps.append((rule, before, after, before - after))

    n0 = len(df)

    # Rule 1: missing CustomerID
    df = df[df["CustomerID"].notna()].copy()
    log("1. remove missing CustomerID", n0, len(df))

    # Rule 2: exact duplicates
    n = len(df)
    df = df.drop_duplicates()
    log("2. remove exact duplicates", n, len(df))

    # Rule 3: cancellations
    n = len(df)
    df = df[~df["InvoiceNo"].str.startswith("C")]
    log("3. remove cancellations (C-invoices)", n, len(df))

    # Rule 4: non-positive prices
    n = len(df)
    df = df[df["UnitPrice"] > 0]
    log("4. remove non-positive prices", n, len(df))

    # Rule 5: administrative stock codes
    n = len(df)
    df = df[~df["StockCode"].str.strip().str.upper().isin(ADMIN_CODES)]
    log("5. remove admin codes (POST, M, C2, DOT, BANK CHARGES)", n, len(df))

    df["CustomerID"] = df["CustomerID"].astype(int)
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]

    if verbose:
        print(f"Raw rows: {n0:,}")
        for rule, before, after, removed in steps:
            print(f"  {rule}: {before:,} -> {after:,}  (-{removed:,})")
        print()
        print(f"Clean invoice lines : {len(df):,}")
        print(f"Customers           : {df['CustomerID'].nunique():,}")
        print(f"Invoices            : {df['InvoiceNo'].nunique():,}")
        print(f"Date range          : {df['InvoiceDate'].min()} -> {df['InvoiceDate'].max()}")
    return df


if __name__ == "__main__":
    df = clean(load_raw())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nSaved {OUT}")
