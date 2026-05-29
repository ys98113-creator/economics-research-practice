"""
03_dashboard.py
Reads silver/cleaned/ data and produces an interactive HTML dashboard
saved to gold/dashboard/consumer_indicators_dashboard.html.

Dashboard sections:
  1. Descriptive Statistics table — all variables
  2. Regional CPI (Inflation) — line chart + bar chart
  3. Regional HPI (Home Prices) — line chart + YoY bar
  4. Real Wages by Region — line chart
  5. Debt Stress — quarterly delinquency rate
  6. Consumer Sentiment — with rolling average
  7. Correlation heatmap — all YoY variables
"""

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
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

def read(fname):
    path = os.path.join(SILVER, fname)
    if not os.path.exists(path):
        return None
    return pd.read_csv(path, index_col="date", parse_dates=True)

# ------------------------------------------------------------------
# Section builders
# ------------------------------------------------------------------

def stats_table(stats_df):
    """Descriptive statistics as a formatted Plotly table."""
    cols_show = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
    cols_show = [c for c in cols_show if c in stats_df.columns]
    tbl = stats_df[cols_show].reset_index()
    tbl[cols_show] = tbl[cols_show].round(2)

    fig = go.Figure(go.Table(
        header=dict(
            values=["<b>Variable</b>"] + [f"<b>{c}</b>" for c in cols_show],
            fill_color="#1f3a5f",
            font=dict(color="white", size=11),
            align="left",
        ),
        cells=dict(
            values=[tbl["variable"]] + [tbl[c] for c in cols_show],
            fill_color=[["#f0f4f8" if i % 2 == 0 else "white"
                         for i in range(len(tbl))]],
            align="left",
            font=dict(size=10),
        )
    ))
    fig.update_layout(title="<b>Descriptive Statistics — All Variables (2021–2026)</b>",
                      margin=dict(t=50, b=10))
    return fig


def cpi_charts(cpi):
    """Regional CPI: index level + YoY inflation rate."""
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
        if yoy_col in cpi.columns:
            fig.add_trace(go.Scatter(x=cpi.index, y=cpi[yoy_col],
                                     name=label, line=dict(color=color),
                                     legendgroup=r, showlegend=False), row=1, col=2)

    fig.update_layout(title="<b>Regional Consumer Price Index (CPI)</b>",
                      height=420, hovermode="x unified")
    fig.update_yaxes(title_text="Index (Jan 2021 = 100)", row=1, col=1)
    fig.update_yaxes(title_text="YoY % Change", row=1, col=2)
    return fig


def hpi_charts(hpi):
    """Regional HPI: index level + YoY change."""
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
        if yoy_col in hpi.columns:
            fig.add_trace(go.Scatter(x=hpi.index, y=hpi[yoy_col],
                                     name=label, line=dict(color=color),
                                     legendgroup=r, showlegend=False), row=1, col=2)

    # National benchmark
    if "hpi_index_national" in hpi.columns:
        fig.add_trace(go.Scatter(x=hpi.index, y=hpi["hpi_index_national"],
                                 name="National", line=dict(color="black", dash="dash"),
                                 legendgroup="national"), row=1, col=1)
    if "hpi_yoy_national" in hpi.columns:
        fig.add_trace(go.Scatter(x=hpi.index, y=hpi["hpi_yoy_national"],
                                 name="National", line=dict(color="black", dash="dash"),
                                 legendgroup="national", showlegend=False), row=1, col=2)

    fig.update_layout(title="<b>Regional Home Price Index (HPI — Case-Shiller Metro Proxies)</b>",
                      height=420, hovermode="x unified")
    fig.update_yaxes(title_text="Index", row=1, col=1)
    fig.update_yaxes(title_text="YoY % Change", row=1, col=2)
    return fig


def wages_chart(wages):
    """Real wages by region."""
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
        if yoy_col in wages.columns:
            fig.add_trace(go.Scatter(x=wages.index, y=wages[yoy_col],
                                     name=label, line=dict(color=color),
                                     legendgroup=r, showlegend=False), row=1, col=2)

    fig.update_layout(title="<b>Real Wages by Region</b>",
                      height=420, hovermode="x unified")
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

    # Add reference line at 80 (roughly neutral)
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
    stats = pd.read_csv(stats_path, index_col="variable") if os.path.exists(stats_path) else None
    cpi       = read("cpi_clean.csv")
    hpi       = read("hpi_clean.csv")
    wages     = read("wages_clean.csv")
    debt      = read("debt_clean.csv")
    sentiment = read("sentiment_clean.csv")
    panel     = read("panel_monthly.csv")

    charts = []

    if stats is not None:
        charts.append(("stats", stats_table(stats)))
    if cpi is not None:
        charts.append(("cpi", cpi_charts(cpi)))
    if hpi is not None:
        charts.append(("hpi", hpi_charts(hpi)))
    if wages is not None:
        charts.append(("wages", wages_chart(wages)))
    if debt is not None:
        charts.append(("debt", debt_chart(debt)))
    if sentiment is not None:
        charts.append(("sentiment", sentiment_chart(sentiment)))
    if panel is not None:
        hm = correlation_heatmap(panel)
        if hm is not None:
            charts.append(("corr", hm))

    if not charts:
        print("No data found in silver/cleaned/. Run 01 and 02 first.")
        return

    # --- Write combined HTML ---
    html_blocks = []
    for _, fig in charts:
        html_blocks.append(fig.to_html(full_html=False, include_plotlyjs="cdn"
                           if _ == charts[0][0] else False))

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
