"""
01_collect_data.py
Pulls 5 years of regional economic data from FRED into bronze/raw_data/.

Variables collected:
  - CPI          : Regional (4 Census regions), monthly
  - HPI          : Regional proxies via Case-Shiller metros, monthly
  - Real Wages   : National AHE deflated by regional CPI, monthly
  - Debt Stress  : National credit card delinquency rate, quarterly
  - Sentiment    : University of Michigan Consumer Sentiment, monthly

Regions: Northeast, Midwest, South, West
"""

import os
import pandas as pd
import pandas_datareader.data as web
from datetime import datetime

START = "2021-01-01"
END   = "2026-05-01"
OUT   = os.path.join(os.path.dirname(__file__), "../bronze/raw_data")

# ------------------------------------------------------------------
# FRED series definitions
# ------------------------------------------------------------------
SERIES = {

    # --- CPI by Census Region (BLS, monthly, SA) ---
    "cpi_northeast": "CUURA100SA0",
    "cpi_midwest":   "CUURA200SA0",
    "cpi_south":     "CUURA300SA0",
    "cpi_west":      "CUURA400SA0",

    # --- Average Hourly Earnings, All Private (BLS, monthly, SA) ---
    # Used to compute real wages when deflated by regional CPI
    "ahe_national":  "CES0500000003",

    # --- Home Price Index (Case-Shiller, monthly, SA) ---
    # Metro proxies for each region
    "hpi_northeast": "NYXRSA",    # New York
    "hpi_south":     "DAXRSA",    # Dallas (South proxy)
    "hpi_midwest":   "CHXRSA",    # Chicago
    "hpi_west":      "LXXRSA",    # Los Angeles
    "hpi_national":  "CSUSHPISA", # 20-city composite (benchmark)

    # --- Consumer Credit Card Delinquency Rate (Fed, quarterly, SA) ---
    "debt_stress":   "DRCCLACBS",

    # --- University of Michigan Consumer Sentiment (monthly) ---
    "sentiment":     "UMCSENT",
}

# ------------------------------------------------------------------
# Pull each series from FRED
# ------------------------------------------------------------------
def pull(series_id, name):
    print(f"  Pulling {name} ({series_id}) ...", end=" ")
    try:
        df = web.DataReader(series_id, "fred", START, END)
        df.columns = [name]
        print(f"OK — {len(df)} rows")
        return df
    except Exception as e:
        print(f"FAILED: {e}")
        return None

def main():
    os.makedirs(OUT, exist_ok=True)
    print(f"\nPulling data from FRED  ({START} → {END})\n")

    frames = {}
    for name, sid in SERIES.items():
        df = pull(sid, name)
        if df is not None:
            frames[name] = df

    if not frames:
        print("\nNo data retrieved. Check your internet connection.")
        return

    # --- Save each group to its own CSV ---
    groups = {
        "cpi_regional":       [k for k in frames if k.startswith("cpi_")],
        "wages_national":     [k for k in frames if k.startswith("ahe_")],
        "hpi_regional":       [k for k in frames if k.startswith("hpi_")],
        "debt_stress":        [k for k in frames if k.startswith("debt_")],
        "consumer_sentiment": [k for k in frames if k == "sentiment"],
    }

    for fname, keys in groups.items():
        subset = {k: frames[k] for k in keys if k in frames}
        if not subset:
            continue
        combined = pd.concat(subset.values(), axis=1)
        combined.index.name = "date"
        path = os.path.join(OUT, f"{fname}.csv")
        combined.to_csv(path)
        print(f"  Saved → {path}  ({combined.shape})")

    print("\nData collection complete.")

if __name__ == "__main__":
    main()
