"""
03_dashboard.py
Reads silver/cleaned/ data and produces an interactive HTML dashboard
saved to gold/dashboard/consumer_indicators_dashboard.html.

Dashboard sections:
  1. Descriptive Statistics table — all variables (hover for description, median added)
  2. Regional CPI (Inflation) — line chart + YoY change (end-of-line region labels)
  3. Regional HPI (Home Prices) — line chart + YoY change (end-of-line region labels)
  4. Real Wages by Region — line chart (end-of-line region labels)
  5. Debt Stress — quarterly delinquency rate
  6. Consumer Sentiment — with rolling average
  7. Correlation heatmap — all YoY variables
"""

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

SILVER = os.path.join(os.path.dirname(__file__), "../silver/cleaned")
GOLD   = os.path.join(os.path.dirname(__file__), "../gold/dashboard")
os.makedirs(GOLD, exist_ok=True)

REGION_COLORS = {
    "northeast": "#1f77b4",
    "midwest":   "#ff7f0e",
    "south":     "#2ca02c",
    "west":      "#d62728",
}
REGION_LABELS = {
    "northeast": "Northeast",
    "midwest":   "Midwest",
    "south":     "South",
    "west":      "West",
}

# ------------------------------------------------------------------
# Variable descriptions shown on hover in the stats table
# ------------------------------------------------------------------
VAR_DESCRIPTIONS = {
    "cpi_yoy_northeast":    "YoY CPI inflation rate — Northeast (urban). How much prices rose vs. a year ago.",
    "cpi_yoy_midwest":      "YoY CPI inflation rate — Midwest (urban). How much prices rose vs. a year ago.",
    "cpi_yoy_south":        "YoY CPI inflation rate — South (urban). How much prices rose vs. a year ago.",
    "cpi_yoy_west":         "YoY CPI inflation rate — West (urban). How much prices rose vs. a year ago.",
    "cpi_index_northeast":  "CPI price level index — Northeast, rebased to 100 at Jan 2021. Shows cumulative inflation since 2021.",
    "cpi_index_midwest":    "CPI price level index — Midwest, rebased to 100 at Jan 2021.",
    "cpi_index_south":      "CPI price level index — South, rebased to 100 at Jan 2021.",
    "cpi_index_west":       "CPI price level index — West, rebased to 100 at Jan 2021.",
    "hpi_yoy_northeast":    "YoY home price growth — Northeast (New York Case-Shiller proxy). How fast home values are rising.",
    "hpi_yoy_south":        "YoY home price growth — South (Dallas Case-Shiller proxy).",
    "hpi_yoy_midwest":      "YoY home price growth — Midwest (Chicago Case-Shiller proxy).",
    "hpi_yoy_west":         "YoY home price growth — West (Los Angeles Case-Shiller proxy).",
    "hpi_yoy_national":     "YoY home price growth — National 20-city composite (S&P/Case-Shiller benchmark).",
    "hpi_index_northeast":  "Home price index — Northeast, rebased to 100 at series start. Tracks cumulative appreciation.",
    "hpi_index_south":      "Home price index — South, rebased to 100 at series start.",
    "hpi_index_midwest":    "Home price index — Midwest, rebased to 100 at series start.",
    "hpi_index_west":       "Home price index — West, rebased to 100 at series start.",
    "hpi_index_national":   "National home price index — 20-city composite, rebased to 100.",
    "real_wage_northeast":  "Real wage (purchasing power) in the Northeast. National average hourly earnings deflated by Northeast CPI.",
    "real_wage_midwest":    "Real wage in the Midwest. National AHE deflated by Midwest CPI.",
    "real_wage_south":      "Real wage in the South. National AHE deflated by South CPI.",
    "real_wage_west":       "Real wage in the West. National AHE deflated by West CPI. West has highest inflation so real wages are lowest.",
    "real_wage_yoy_northeast": "YoY real wage growth — Northeast. Positive means workers are gaining purchasing power.",
    "real_wage_yoy_midwest":   "YoY real wage growth — Midwest.",
    "real_wage_yoy_south":     "YoY real wage growth — South.",
    "real_wage_yoy_west":      "YoY real wage growth — West.",
    "nominal_wage":         "National average hourly earnings (not inflation-adjusted). Source: BLS Current Employment Statistics.",
    "debt_delinquency_rate":"Share of credit card balances 30+ days past due. Rising = consumers under financial stress.",
    "debt_4q_avg":          "4-quarter rolling average of the credit card delinquency rate. Smooths seasonal noise.",
    "debt_yoy_chg":         "YoY change in delinquency rate (percentage points). Positive = stress worsening vs. a year ago.",
    "sentiment":            "University of Michigan Consumer Sentiment Index. Above 80 = broadly optimistic; below 70 = notable pessimism.",
    "sentiment_12m_avg":    "12-month rolling average of consumer sentiment. Filters monthly volatility to reveal the trend.",
    "sentiment_yoy_chg":    "YoY change in sentiment (index points). Negative = consumers more pessimistic than a year ago.",
}

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def read(fname):
    path = os.path.join(SILVER, fname)
    if not os.path.exists(path):
        return None
    return pd.read_csv(path, index_col="date", parse_dates=True)


def _add_end_label(fig, df, col, label, color, subplot_col=1):
    """Add a color-matched region label at the last data point of a line."""
    s = df[col].dropna()
    if s.empty:
        return
    suffix = "" if subplot_col == 1 else str(subplot_col)
    fig.add_annotation(
        x=s.index[-1],
        y=s.iloc[-1],
        text=f"  <b>{label}</b>",
        xref=f"x{suffix}",
        yref=f"y{suffix}",
        showarrow=False,
        font=dict(color=color, size=9),
        xanchor="left",
        bgcolor="rgba(255,255,255,0.75)",
    )


# ------------------------------------------------------------------
# Section builders
# ------------------------------------------------------------------

def stats_table_html(stats_df):
    """
    Build stats table as a styled HTML string.
    Hover over any variable name to see its description (via CSS tooltip).
    Returns a raw HTML string (not a Plotly figure).
    """
    cols_show    = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
    cols_show    = [c for c in cols_show if c in stats_df.columns]
    header_names = {"50%": "Median"}

    tbl = stats_df[cols_show].reset_index()
    tbl[cols_show] = tbl[cols_show].round(2)

    # Table header row
    th_cells = "<th>Variable <span style='font-weight:normal;font-size:10px;color:#aaa'>(hover for description)</span></th>"
    for c in cols_show:
        th_cells += f"<th>{header_names.get(c, c)}</th>"

    # Data rows
    rows_html = ""
    for i, row in tbl.iterrows():
        var   = row["variable"]
        desc  = VAR_DESCRIPTIONS.get(var, "No description available.")
        bg    = "#f0f4f8" if i % 2 == 0 else "#ffffff"
        # Variable cell with CSS tooltip
        var_cell = (
            f'<td class="var-cell" style="background:{bg}">'
            f'<span class="tooltip-wrap">{var}'
            f'<span class="tooltip-box">{desc}</span>'
            f'</span></td>'
        )
        num_cells = "".join(
            f'<td style="background:{bg}">{row[c]}</td>' for c in cols_show
        )
        rows_html += f"<tr>{var_cell}{num_cells}</tr>\n"

    return f"""
<style>
  .stats-title {{ font-family: -apple-system, sans-serif; font-size:15px;
                  font-weight:600; color:#1f3a5f; margin-bottom:10px; }}
  .stats-wrap  {{ overflow-x:auto; }}
  .stats-tbl   {{ border-collapse:collapse; width:100%;
                  font-family: -apple-system, sans-serif; font-size:11px; }}
  .stats-tbl th {{ background:#1f3a5f; color:#fff; padding:8px 10px;
                   text-align:left; position:sticky; top:0; white-space:nowrap; }}
  .stats-tbl td {{ padding:6px 10px; white-space:nowrap; border-bottom:1px solid #e8ecf0; }}
  .var-cell     {{ position:relative; cursor:help; }}
  .tooltip-wrap {{ position:relative; display:inline-block; }}
  .tooltip-wrap .tooltip-box {{
    display:none; position:absolute; left:100%; top:-4px; z-index:999;
    background:#1f3a5f; color:#fff; font-size:11px; line-height:1.5;
    padding:8px 12px; border-radius:6px; width:280px;
    box-shadow:0 4px 12px rgba(0,0,0,.2);
    white-space:normal;
  }}
  .tooltip-wrap:hover .tooltip-box {{ display:block; }}
</style>
<div class="stats-title">
  Descriptive Statistics — All Variables (2021–2026)
</div>
<div class="stats-wrap">
  <table class="stats-tbl">
    <thead><tr>{th_cells}</tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>"""


def cpi_charts(cpi):
    """Regional CPI: index level + YoY inflation rate with end-of-line labels."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("CPI Index (rebased to 100 = Jan 2021)",
                        "Inflation Rate — YoY % Change"),
        shared_xaxes=False,
    )
    for r in ["northeast", "midwest", "south", "west"]:
        idx_col = f"cpi_index_{r}"
        yoy_col = f"cpi_yoy_{r}"
        label   = REGION_LABELS[r]
        color   = REGION_COLORS[r]

        if idx_col in cpi.columns:
            fig.add_trace(go.Scatter(x=cpi.index, y=cpi[idx_col],
                                     name=label, line=dict(color=color),
                                     legendgroup=r), row=1, col=1)
            _add_end_label(fig, cpi, idx_col, label, color, subplot_col=1)

        if yoy_col in cpi.columns:
            fig.add_trace(go.Scatter(x=cpi.index, y=cpi[yoy_col],
                                     name=label, line=dict(color=color),
                                     legendgroup=r, showlegend=False), row=1, col=2)
            _add_end_label(fig, cpi, yoy_col, label, color, subplot_col=2)

    fig.update_layout(
        title="<b>Regional Consumer Price Index (CPI)</b>"
              "<br><sup>Colors: "
              "<span style='color:#1f77b4'>■ Northeast</span>  "
              "<span style='color:#ff7f0e'>■ Midwest</span>  "
              "<span style='color:#2ca02c'>■ South</span>  "
              "<span style='color:#d62728'>■ West</span></sup>",
        height=440, hovermode="x unified", margin=dict(r=90),
    )
    fig.update_yaxes(title_text="Index (Jan 2021 = 100)", row=1, col=1)
    fig.update_yaxes(title_text="YoY % Change", row=1, col=2)
    return fig


def hpi_charts(hpi):
    """Regional HPI: index level + YoY change with end-of-line labels."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("HPI Index (rebased to 100 = first observation)",
                        "Home Price Growth — YoY % Change"),
    )
    for r in ["northeast", "midwest", "south", "west"]:
        idx_col = f"hpi_index_{r}"
        yoy_col = f"hpi_yoy_{r}"
        label   = REGION_LABELS[r]
        color   = REGION_COLORS[r]

        if idx_col in hpi.columns:
            fig.add_trace(go.Scatter(x=hpi.index, y=hpi[idx_col],
                                     name=label, line=dict(color=color),
                                     legendgroup=r), row=1, col=1)
            _add_end_label(fig, hpi, idx_col, label, color, subplot_col=1)

        if yoy_col in hpi.columns:
            fig.add_trace(go.Scatter(x=hpi.index, y=hpi[yoy_col],
                                     name=label, line=dict(color=color),
                                     legendgroup=r, showlegend=False), row=1, col=2)
            _add_end_label(fig, hpi, yoy_col, label, color, subplot_col=2)

    # National benchmark
    if "hpi_index_national" in hpi.columns:
        fig.add_trace(go.Scatter(x=hpi.index, y=hpi["hpi_index_national"],
                                 name="National", line=dict(color="black", dash="dash"),
                                 legendgroup="national"), row=1, col=1)
        _add_end_label(fig, hpi, "hpi_index_national", "National", "black", subplot_col=1)
    if "hpi_yoy_national" in hpi.columns:
        fig.add_trace(go.Scatter(x=hpi.index, y=hpi["hpi_yoy_national"],
                                 name="National", line=dict(color="black", dash="dash"),
                                 legendgroup="national", showlegend=False), row=1, col=2)
        _add_end_label(fig, hpi, "hpi_yoy_national", "National", "black", subplot_col=2)

    fig.update_layout(
        title="<b>Regional Home Price Index (HPI — Case-Shiller Metro Proxies)</b>"
              "<br><sup>Colors: "
              "<span style='color:#1f77b4'>■ Northeast (NYC)</span>  "
              "<span style='color:#ff7f0e'>■ Midwest (Chicago)</span>  "
              "<span style='color:#2ca02c'>■ South (Dallas)</span>  "
              "<span style='color:#d62728'>■ West (LA)</span>  "
              "<span style='color:#000'>-- National</span></sup>",
        height=440, hovermode="x unified", margin=dict(r=90),
    )
    fig.update_yaxes(title_text="Index", row=1, col=1)
    fig.update_yaxes(title_text="YoY % Change", row=1, col=2)
    return fig


def wages_chart(wages):
    """Real wages by region with end-of-line labels."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Real Wage Level (Nominal AHE deflated by regional CPI)",
                        "Real Wage Growth — YoY % Change"),
    )
    for r in ["northeast", "midwest", "south", "west"]:
        lvl_col = f"real_wage_{r}"
        yoy_col = f"real_wage_yoy_{r}"
        label   = REGION_LABELS[r]
        color   = REGION_COLORS[r]

        if lvl_col in wages.columns:
            fig.add_trace(go.Scatter(x=wages.index, y=wages[lvl_col],
                                     name=label, line=dict(color=color),
                                     legendgroup=r), row=1, col=1)
            _add_end_label(fig, wages, lvl_col, label, color, subplot_col=1)

        if yoy_col in wages.columns:
            fig.add_trace(go.Scatter(x=wages.index, y=wages[yoy_col],
                                     name=label, line=dict(color=color),
                                     legendgroup=r, showlegend=False), row=1, col=2)
            _add_end_label(fig, wages, yoy_col, label, color, subplot_col=2)

    fig.update_layout(
        title="<b>Real Wages by Region</b>"
              "<br><sup>Colors: "
              "<span style='color:#1f77b4'>■ Northeast</span>  "
              "<span style='color:#ff7f0e'>■ Midwest</span>  "
              "<span style='color:#2ca02c'>■ South</span>  "
              "<span style='color:#d62728'>■ West</span></sup>",
        height=440, hovermode="x unified", margin=dict(r=90),
    )
    fig.update_yaxes(title_text="USD/hour", row=1, col=1)
    fig.update_yaxes(title_text="YoY % Change", row=1, col=2)
    return fig


def debt_chart(debt):
    """Debt stress — credit card delinquency rate."""
    fig = go.Figure()
    if "debt_delinquency_rate" in debt.columns:
        fig.add_trace(go.Scatter(
            x=debt.index, y=debt["debt_delinquency_rate"],
            name="Delinquency Rate", line=dict(color="#d62728"),
            fill="tozeroy", fillcolor="rgba(214,39,40,0.15)",
        ))
    if "debt_4q_avg" in debt.columns:
        fig.add_trace(go.Scatter(
            x=debt.index, y=debt["debt_4q_avg"],
            name="4-Quarter Rolling Avg", line=dict(color="#1f3a5f", dash="dash"),
        ))

    fig.update_layout(
        title="<b>Consumer Debt Stress — Credit Card Delinquency Rate (Quarterly)</b>",
        yaxis_title="Delinquency Rate (%)",
        height=380,
        hovermode="x unified",
        annotations=[dict(
            text="Note: Quarterly data forward-filled to monthly frequency",
            xref="paper", yref="paper", x=0, y=-0.12,
            showarrow=False, font=dict(size=10, color="gray"),
        )],
    )
    return fig


def sentiment_chart(sentiment):
    """Consumer sentiment with rolling average."""
    fig = go.Figure()
    if "sentiment" in sentiment.columns:
        fig.add_trace(go.Scatter(
            x=sentiment.index, y=sentiment["sentiment"],
            name="Monthly Sentiment", line=dict(color="#7f7f7f", width=1),
            opacity=0.6,
        ))
    if "sentiment_12m_avg" in sentiment.columns:
        fig.add_trace(go.Scatter(
            x=sentiment.index, y=sentiment["sentiment_12m_avg"],
            name="12-Month Rolling Avg", line=dict(color="#1f77b4", width=2.5),
        ))

    fig.add_hline(y=80, line_dash="dot", line_color="green",
                  annotation_text="Neutral (~80)", annotation_position="bottom right")

    fig.update_layout(
        title="<b>University of Michigan Consumer Sentiment (National)</b>",
        yaxis_title="Index",
        height=380,
        hovermode="x unified",
    )
    return fig


def correlation_heatmap(panel):
    """Correlation matrix of all YoY variables."""
    yoy_cols = [c for c in panel.columns if "yoy" in c or "sentiment" in c
                or "debt" in c]
    sub = panel[yoy_cols].dropna(how="all")
    if sub.shape[1] < 2:
        return None

    corr = sub.corr().round(2)
    labels = corr.columns.tolist()

    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=labels,
        y=labels,
        colorscale="RdBu",
        zmid=0,
        text=corr.values.round(2),
        texttemplate="%{text}",
        colorbar=dict(title="r"),
    ))
    fig.update_layout(
        title="<b>Correlation Matrix — YoY Change Variables</b>",
        height=550,
        xaxis=dict(tickangle=45),
    )
    return fig


# ------------------------------------------------------------------
# Assemble full dashboard
# ------------------------------------------------------------------
def build_dashboard():
    print("\nBuilding dashboard  (silver → gold)\n")

    stats_path = os.path.join(SILVER, "descriptive_stats.csv")
    stats     = pd.read_csv(stats_path, index_col="variable") if os.path.exists(stats_path) else None
    cpi       = read("cpi_clean.csv")
    hpi       = read("hpi_clean.csv")
    wages     = read("wages_clean.csv")
    debt      = read("debt_clean.csv")
    sentiment = read("sentiment_clean.csv")
    panel     = read("panel_monthly.csv")

    # Stats table is HTML; all others are Plotly figures
    stats_html = stats_table_html(stats) if stats is not None else None

    plotly_charts = []
    if cpi is not None:
        plotly_charts.append(("cpi", cpi_charts(cpi)))
    if hpi is not None:
        plotly_charts.append(("hpi", hpi_charts(hpi)))
    if wages is not None:
        plotly_charts.append(("wages", wages_chart(wages)))
    if debt is not None:
        plotly_charts.append(("debt", debt_chart(debt)))
    if sentiment is not None:
        plotly_charts.append(("sentiment", sentiment_chart(sentiment)))
    if panel is not None:
        hm = correlation_heatmap(panel)
        if hm is not None:
            plotly_charts.append(("corr", hm))

    if stats_html is None and not plotly_charts:
        print("No data found in silver/cleaned/. Run 01 and 02 first.")
        return

    html_blocks = []
    # Stats table first (raw HTML block)
    if stats_html:
        html_blocks.append(stats_html)
    # Plotly charts
    first = True
    for name, fig in plotly_charts:
        html_blocks.append(fig.to_html(
            full_html=False,
            include_plotlyjs="cdn" if first else False,
        ))
        first = False

    full_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>U.S. Consumer Spending Indicators Dashboard</title>
  <style>
    body   {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif;
              background: #f5f7fa; margin: 0; padding: 20px; }}
    h1     {{ color: #1f3a5f; border-bottom: 3px solid #1f77b4;
              padding-bottom: 10px; }}
    p.sub  {{ color: #555; font-size: 13px; margin-top: -10px; }}
    .card  {{ background: white; border-radius: 8px;
              box-shadow: 0 2px 8px rgba(0,0,0,.08);
              padding: 16px; margin-bottom: 24px; }}
    footer {{ color: #aaa; font-size: 11px; text-align: center;
              margin-top: 30px; }}
  </style>
</head>
<body>
  <h1>U.S. Consumer Spending Indicators — Regional Dashboard</h1>
  <p class="sub">
    Variables: CPI (4 regions) &nbsp;|&nbsp; HPI (metro proxies) &nbsp;|&nbsp;
    Real Wages &nbsp;|&nbsp; Debt Stress &nbsp;|&nbsp; Consumer Sentiment
    &nbsp;&nbsp;·&nbsp;&nbsp; Period: 2021 – 2026
  </p>
  {''.join(f'<div class="card">{block}</div>' for block in html_blocks)}
  <footer>
    Sources: BLS, FHFA, S&amp;P Case-Shiller, Federal Reserve, University of Michigan
    via FRED (St. Louis Fed) &nbsp;·&nbsp; Built with Python + Plotly
  </footer>
</body>
</html>"""

    out_path = os.path.join(GOLD, "consumer_indicators_dashboard.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"  Dashboard saved → {out_path}")
    print(f"\nOpen in browser:  open \"{out_path}\"")

if __name__ == "__main__":
    build_dashboard()
