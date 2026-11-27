"""Step 0 - Download the UCI Online Retail dataset and convert it to CSV.

Dataset: UCI Machine Learning Repository #352 "Online Retail"
Transactions of a UK-based online retailer, 01/Dec/2010 - 09/Dec/2011.
"""
import io
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen

URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
XLSX = RAW / "Online Retail.xlsx"
CSV = RAW / "online_retail_raw.csv"


def download() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    if XLSX.exists():
        print(f"Already downloaded: {XLSX}")
        return
    print("Downloading", URL)
    data = urlopen(URL).read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(RAW)
    print(f"Saved {XLSX}")


def convert() -> None:
    import pandas as pd

    if CSV.exists():
        print(f"Already converted: {CSV}")
        return
    print("Converting xlsx -> csv (takes a minute) ...")
    df = pd.read_excel(XLSX, dtype={"InvoiceNo": str, "StockCode": str})
    df.to_csv(CSV, index=False)
    print(f"Saved {CSV}  ({len(df):,} rows)")


if __name__ == "__main__":
    download()
    convert()
