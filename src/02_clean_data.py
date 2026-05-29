"""
02_clean_data.py
Reads bronze/raw_data/ CSVs, cleans and standardizes each variable,
then writes analysis-ready files to silver/cleaned/.

Cleaning steps per variable:
  CPI          : Compute YoY % change (inflation rate) per region
  HPI          : Compute YoY % change per region; rebase index to 2021-01
  Real Wages   : Deflate national AHE by regional CPI → 4 regional real wage series
  Debt Stress  : Forward-fill quarterly to monthly; compute 4-quarter rolling avg
  Sentiment    : Drop nulls; compute 12-month rolling average

Final output:
  silver/cleaned/panel_monthly.csv  — all monthly variables merged (long format)
  silver/cleaned/panel_quarterly.csv — all variables at quarterly frequency
  silver/cleaned/descriptive_stats.csv — summary statistics per variable per region
"""

import os
import pandas as pd
import numpy as np

BRONZE = os.path.join(os.path.dirname(__file__), "../bronze/raw_data")
SILVER = os.path.join(os.path.dirname(__file__), "../silver/cleaned")
os.makedirs(SILVER, exist_ok=True)

REGIONS = ["northeast", "midwest", "south", "west"]

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def read(fname):
    path = os.path.join(BRONZE, fname)
    if not os.path.exists(path):
        print(f"  WARNING: {fname} not found, skipping.")
        return None
    df = pd.read_csv(path, index_col="date", parse_dates=True)
    return df

def yoy_pct(series):
    """Year-over-year percentage change."""
    return series.pct_change(12) * 100

def rebase(series, base_date="2021-01-01"):
    """Rebase index so base_date = 100."""
    base = series.asof(pd.Timestamp(base_date))
    if pd.isna(base) or base == 0:
        return series
    return (series / base) * 100

# ------------------------------------------------------------------
# 1. CPI — Regional Inflation Rate (YoY %)
# ------------------------------------------------------------------
def clean_cpi(raw):
    print("  Cleaning CPI ...")
    out = pd.DataFrame(index=raw.index)
    for r in REGIONS:
        col = f"cpi_{r}"
        if col in raw.columns:
            out[f"cpi_yoy_{r}"] = yoy_pct(raw[col])
            out[f"cpi_index_{r}"] = rebase(raw[col])
    out.index.name = "date"
    out.to_csv(os.path.join(SILVER, "cpi_clean.csv"))
    print(f"    → cpi_clean.csv  {out.shape}")
    return out

# ------------------------------------------------------------------
# 2. HPI — Regional Home Price Change (YoY %)
# ------------------------------------------------------------------
def clean_hpi(raw):
    print("  Cleaning HPI ...")
    out = pd.DataFrame(index=raw.index)
    for r in REGIONS:
        col = f"hpi_{r}"
        if col in raw.columns:
            out[f"hpi_yoy_{r}"] = yoy_pct(raw[col])
            out[f"hpi_index_{r}"] = rebase(raw[col])
    if "hpi_national" in raw.columns:
        out["hpi_yoy_national"] = yoy_pct(raw["hpi_national"])
        out["hpi_index_national"] = rebase(raw["hpi_national"])
    out.index.name = "date"
    out.to_csv(os.path.join(SILVER, "hpi_clean.csv"))
    print(f"    → hpi_clean.csv  {out.shape}")
    return out

# ------------------------------------------------------------------
# 3. Real Wages — National AHE deflated by regional CPI
# ------------------------------------------------------------------
def clean_wages(raw_wages, raw_cpi):
    print("  Cleaning Real Wages ...")
    if raw_wages is None or "ahe_national" not in raw_wages.columns:
        print("    WARNING: wage data missing.")
        return None

    out = pd.DataFrame(index=raw_wages.index)
    nominal = raw_wages["ahe_national"]

    for r in REGIONS:
        cpi_col = f"cpi_{r}"
        if raw_cpi is not None and cpi_col in raw_cpi.columns:
            cpi = raw_cpi[cpi_col].reindex(nominal.index, method="ffill")
            # Real wage: nominal / (CPI / 100)
            out[f"real_wage_{r}"] = nominal / (cpi / cpi.iloc[0])
        else:
            out[f"real_wage_{r}"] = nominal  # fallback

    # YoY % change
    for r in REGIONS:
        col = f"real_wage_{r}"
        if col in out.columns:
            out[f"real_wage_yoy_{r}"] = yoy_pct(out[col])

    out["nominal_wage"] = nominal
    out.index.name = "date"
    out.to_csv(os.path.join(SILVER, "wages_clean.csv"))
    print(f"    → wages_clean.csv  {out.shape}")
    return out

# ------------------------------------------------------------------
# 4. Debt Stress — Quarterly → forward-filled to monthly
# ------------------------------------------------------------------
def clean_debt(raw):
    print("  Cleaning Debt Stress ...")
    if raw is None or "debt_stress" not in raw.columns:
        print("    WARNING: debt stress data missing.")
        return None

    s = raw["debt_stress"].dropna()

    # Reindex to monthly, forward-fill (quarterly reading holds until next)
    monthly_idx = pd.date_range(s.index.min(), s.index.max(), freq="MS")
    s_monthly = s.reindex(monthly_idx, method="ffill")

    out = pd.DataFrame({
        "debt_delinquency_rate": s_monthly,
        "debt_4q_avg": s_monthly.rolling(4).mean(),
        "debt_yoy_chg": s_monthly.diff(4),
    })
    out.index.name = "date"
    out.to_csv(os.path.join(SILVER, "debt_clean.csv"))
    print(f"    → debt_clean.csv  {out.shape}")
    return out

# ------------------------------------------------------------------
# 5. Consumer Sentiment
# ------------------------------------------------------------------
def clean_sentiment(raw):
    print("  Cleaning Consumer Sentiment ...")
    if raw is None or "sentiment" not in raw.columns:
        print("    WARNING: sentiment data missing.")
        return None

    s = raw["sentiment"].dropna()
    out = pd.DataFrame({
        "sentiment": s,
        "sentiment_12m_avg": s.rolling(12).mean(),
        "sentiment_yoy_chg": s.diff(12),
    })
    out.index.name = "date"
    out.to_csv(os.path.join(SILVER, "sentiment_clean.csv"))
    print(f"    → sentiment_clean.csv  {out.shape}")
    return out

# ------------------------------------------------------------------
# 6. Merge into panel + descriptive stats
# ------------------------------------------------------------------
def build_panel(cpi, hpi, wages, debt, sentiment):
    print("  Building panel datasets ...")
    pieces = [df for df in [cpi, hpi, wages, debt, sentiment] if df is not None]
    if not pieces:
        print("    No data to merge.")
        return

    panel = pd.concat(pieces, axis=1).sort_index()
    panel.index.name = "date"

    # Monthly panel
    panel.to_csv(os.path.join(SILVER, "panel_monthly.csv"))
    print(f"    → panel_monthly.csv  {panel.shape}")

    # Quarterly panel (resample to quarter-end mean)
    panel_q = panel.resample("Q").mean()
    panel_q.to_csv(os.path.join(SILVER, "panel_quarterly.csv"))
    print(f"    → panel_quarterly.csv  {panel_q.shape}")

    # Descriptive statistics
    stats = panel.describe().T
    stats["skew"]     = panel.skew()
    stats["kurtosis"] = panel.kurtosis()
    stats.index.name  = "variable"
    stats.to_csv(os.path.join(SILVER, "descriptive_stats.csv"))
    print(f"    → descriptive_stats.csv  {stats.shape}")

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    print("\nCleaning data  (bronze → silver)\n")

    raw_cpi       = read("cpi_regional.csv")
    raw_hpi       = read("hpi_regional.csv")
    raw_wages     = read("wages_national.csv")
    raw_debt      = read("debt_stress.csv")
    raw_sentiment = read("consumer_sentiment.csv")

    cpi       = clean_cpi(raw_cpi)       if raw_cpi is not None       else None
    hpi       = clean_hpi(raw_hpi)       if raw_hpi is not None       else None
    wages     = clean_wages(raw_wages, raw_cpi)
    debt      = clean_debt(raw_debt)     if raw_debt is not None      else None
    sentiment = clean_sentiment(raw_sentiment) if raw_sentiment is not None else None

    build_panel(cpi, hpi, wages, debt, sentiment)
    print("\nCleaning complete.")

if __name__ == "__main__":
    main()
