from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "new"
OUTPUT_DIR = ROOT / "eda_outputs" / "new_csv"
CHART_DIR = OUTPUT_DIR / "charts"

COUNTRY_ISO3 = {
    "Australia": "AUS",
    "Brazil": "BRA",
    "Canada": "CAN",
    "China": "CHN",
    "France": "FRA",
    "Germany": "DEU",
    "India": "IND",
    "Japan": "JPN",
    "Malaysia": "MYS",
    "Mexico": "MEX",
    "Singapore": "SGP",
    "South Korea": "KOR",
    "UK": "GBR",
    "USA": "USA",
    "Vietnam": "VNM",
}

ISO2_TO_ISO3 = {
    "AU": "AUS",
    "BR": "BRA",
    "CA": "CAN",
    "CN": "CHN",
    "DE": "DEU",
    "FR": "FRA",
    "GB": "GBR",
    "IN": "IND",
    "JP": "JPN",
    "KR": "KOR",
    "MX": "MEX",
    "MY": "MYS",
    "SG": "SGP",
    "US": "USA",
    "VN": "VNM",
}

PERIOD_ORDER = ["Pre-Trade War", "Trade War 1.0", "Recovery", "Trade War 2.0"]
ERA_ORDER = ["Pre-Trade War", "Trade War 1.0", "Recovery", "Trade War 2.0"]


def load_csv(name: str, parse_dates: Iterable[str] = ()) -> pd.DataFrame:
    path = DATA_DIR / name
    df = pd.read_csv(path)
    for col in parse_dates:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def add_section(sections: list[str], title: str, body: str = "") -> None:
    sections.append(f"<section><h2>{escape(title)}</h2>{body}")


def close_section(sections: list[str]) -> None:
    sections.append("</section>")


def write_chart(fig: go.Figure, filename: str, title: str, sections: list[str], note: str = "") -> None:
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Arial, sans-serif", size=12),
        title=dict(font=dict(size=20), x=0.01),
        margin=dict(l=52, r=28, t=64, b=52),
    )
    html_path = CHART_DIR / f"{filename}.html"
    fig.write_html(html_path, include_plotlyjs="cdn", full_html=True)

    note_html = f"<p class='chart-note'>{escape(note)}</p>" if note else ""
    sections.append(
        "<article class='chart-card'>"
        f"<h3>{escape(title)}</h3>"
        f"{note_html}"
        f"{fig.to_html(include_plotlyjs=False, full_html=False)}"
        f"<p class='chart-link'><a href='charts/{escape(filename)}.html'>Open standalone chart</a></p>"
        "</article>"
    )


def summarize_dataset(name: str, df: pd.DataFrame) -> dict:
    date_cols = [col for col in df.columns if "date" in col.lower()]
    year_cols = [col for col in df.columns if col.lower() == "year"]
    date_range = ""
    if date_cols:
        parsed = pd.to_datetime(df[date_cols[0]], errors="coerce")
        date_range = f"{parsed.min().date()} to {parsed.max().date()}"
    elif year_cols:
        date_range = f"{int(df[year_cols[0]].min())} to {int(df[year_cols[0]].max())}"
    return {
        "file": name,
        "rows": len(df),
        "columns": len(df.columns),
        "numeric_columns": len(df.select_dtypes(include="number").columns),
        "categorical_columns": len(df.select_dtypes(exclude="number").columns),
        "missing_cells": int(df.isna().sum().sum()),
        "missing_pct": round(float(df.isna().sum().sum() / (df.shape[0] * df.shape[1]) * 100), 2),
        "duplicate_rows": int(df.duplicated().sum()),
        "time_range": date_range,
    }


def make_overview(files: dict[str, pd.DataFrame], sections: list[str]) -> pd.DataFrame:
    rows = [summarize_dataset(name, df) for name, df in files.items()]
    overview = pd.DataFrame(rows).sort_values("rows", ascending=False)

    add_section(
        sections,
        "1. Dataset Overview",
        "<p>High-level structure, completeness, and scale across the CSV files in <code>new/</code>.</p>",
    )

    fig = px.bar(
        overview,
        x="file",
        y="rows",
        color="columns",
        title="Rows by dataset",
        labels={"file": "", "rows": "Rows", "columns": "Columns"},
        text="rows",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_yaxes(type="log", title="Rows (log scale)")
    write_chart(fig, "overview_rows_by_dataset", "Rows by dataset", sections)

    fig = px.bar(
        overview,
        x="file",
        y="missing_pct",
        color="duplicate_rows",
        title="Missing cells and duplicate rows",
        labels={"file": "", "missing_pct": "Missing cells (%)", "duplicate_rows": "Duplicate rows"},
        text="missing_pct",
    )
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    write_chart(fig, "overview_missingness", "Missingness overview", sections)

    dtype_long = overview.melt(
        id_vars="file",
        value_vars=["numeric_columns", "categorical_columns"],
        var_name="column_type",
        value_name="count",
    )
    fig = px.bar(
        dtype_long,
        x="file",
        y="count",
        color="column_type",
        barmode="stack",
        title="Column type mix by dataset",
        labels={"file": "", "count": "Columns", "column_type": "Type"},
    )
    write_chart(fig, "overview_column_types", "Column type mix", sections)

    sections.append(overview.to_html(index=False, classes="summary-table"))
    close_section(sections)
    return overview


def make_column_metadata_charts(df: pd.DataFrame, sections: list[str]) -> None:
    add_section(
        sections,
        "2. Column Metadata",
        "<p>The metadata file documents each source table and supports dashboard field labeling.</p>",
    )
    counts = df.groupby("file", as_index=False).agg(columns=("column", "count"))
    fig = px.bar(counts, x="file", y="columns", title="Documented columns by file", text="columns")
    fig.update_traces(textposition="outside")
    write_chart(fig, "metadata_columns_by_file", "Documented columns by file", sections)

    dtype_counts = df.groupby(["file", "dtype"], as_index=False).size()
    fig = px.bar(
        dtype_counts,
        x="file",
        y="size",
        color="dtype",
        barmode="stack",
        title="Documented data types by file",
        labels={"size": "Columns", "file": "", "dtype": "Documented dtype"},
    )
    write_chart(fig, "metadata_dtype_by_file", "Documented data types", sections)
    close_section(sections)


def make_tariff_charts(df: pd.DataFrame, sections: list[str]) -> None:
    add_section(
        sections,
        "3. Tariff Timeline",
        "<p>Event-level tariff actions, rates, retaliation status, and estimated affected trade value.</p>",
    )
    plot_df = df.copy()
    plot_df["retaliation_label"] = plot_df["retaliation"].map({True: "Retaliation", False: "Initial or policy action"})
    plot_df["bubble_trade_value"] = plot_df["estimated_trade_value_usd_bn"].fillna(0).clip(lower=1)

    fig = px.scatter(
        plot_df,
        x="date",
        y="tariff_rate_pct",
        color="type",
        size="bubble_trade_value",
        hover_data=["imposing_country", "target_country", "sector", "legal_basis", "notes"],
        title="Tariff announcements over time",
        labels={"tariff_rate_pct": "Tariff rate (%)", "date": "", "bubble_trade_value": "Trade value (USD bn)"},
    )
    write_chart(fig, "tariff_timeline_bubble", "Tariff announcement timeline", sections)

    sector_value = (
        plot_df.groupby("sector", as_index=False)["estimated_trade_value_usd_bn"].sum()
        .sort_values("estimated_trade_value_usd_bn", ascending=False)
        .head(20)
    )
    fig = px.bar(
        sector_value,
        x="estimated_trade_value_usd_bn",
        y="sector",
        orientation="h",
        title="Top sectors by estimated affected trade value",
        labels={"estimated_trade_value_usd_bn": "USD billions", "sector": ""},
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    write_chart(fig, "tariff_sector_trade_value", "Affected trade value by sector", sections)

    matrix = plot_df.pivot_table(
        index="imposing_country",
        columns="target_country",
        values="estimated_trade_value_usd_bn",
        aggfunc="sum",
        fill_value=0,
    )
    fig = px.imshow(
        matrix,
        aspect="auto",
        color_continuous_scale="YlOrRd",
        title="Estimated affected trade value: imposing vs target country",
        labels=dict(x="Target country", y="Imposing country", color="USD bn"),
    )
    write_chart(fig, "tariff_country_heatmap", "Tariff relationship heatmap", sections)

    fig = px.histogram(
        plot_df,
        x="tariff_rate_delta",
        color="retaliation_label",
        nbins=24,
        title="Distribution of tariff rate changes",
        labels={"tariff_rate_delta": "Rate change (%)", "retaliation_label": ""},
    )
    write_chart(fig, "tariff_delta_distribution", "Tariff-rate change distribution", sections)

    type_counts = plot_df.groupby(["year", "type"], as_index=False).size()
    fig = px.bar(
        type_counts,
        x="year",
        y="size",
        color="type",
        title="Tariff actions by year and type",
        labels={"size": "Actions", "year": "", "type": "Action type"},
    )
    write_chart(fig, "tariff_actions_by_year", "Tariff actions by year", sections)
    close_section(sections)


def make_trade_volume_charts(df: pd.DataFrame, sections: list[str]) -> None:
    add_section(
        sections,
        "4. Annual Trade and Macro Indicators",
        "<p>Annual country-level indicators including trade flows, GDP, inflation, unemployment, FDI, and current account balance.</p>",
    )
    plot_df = df.copy()
    plot_df["iso3"] = plot_df["country_code"].map(ISO2_TO_ISO3)

    coverage = plot_df.pivot_table(index="country", columns="indicator_name", values="value", aggfunc="count", fill_value=0)
    fig = px.imshow(
        coverage,
        aspect="auto",
        color_continuous_scale="Teal",
        title="Indicator coverage by country",
        labels=dict(x="Indicator", y="Country", color="Rows"),
    )
    write_chart(fig, "trade_indicator_coverage", "Indicator coverage heatmap", sections)

    exports_imports = plot_df[plot_df["indicator_name"].isin([
        "Exports of goods & services (USD)",
        "Imports of goods & services (USD)",
    ])].copy()
    fig = px.line(
        exports_imports,
        x="year",
        y="value",
        color="country",
        facet_row="indicator_name",
        title="Exports and imports by country",
        labels={"value": "US dollars", "year": "", "country": "Country", "indicator_name": ""},
    )
    fig.update_yaxes(matches=None, tickformat="~s")
    write_chart(fig, "trade_exports_imports_lines", "Exports/imports annual trends", sections)

    for indicator in sorted(plot_df["indicator_name"].dropna().unique()):
        indicator_df = plot_df[plot_df["indicator_name"] == indicator].copy()
        fig = px.line(
            indicator_df,
            x="year",
            y="value",
            color="country",
            line_group="country",
            title=f"{indicator} by country",
            labels={"value": "Value", "year": "", "country": "Country"},
        )
        fig.update_yaxes(tickformat="~s")
        slug = (
            indicator.lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("%", "pct")
            .replace("&", "and")
            .replace("(", "")
            .replace(")", "")
            .replace(".", "")
        )
        write_chart(fig, f"trade_indicator_{slug}", indicator, sections)

    latest_year = int(plot_df["year"].max())
    latest = plot_df[plot_df["year"] == latest_year].copy()
    for indicator in ["Exports of goods & services (USD)", "Imports of goods & services (USD)", "Trade (% of GDP)"]:
        latest_ind = latest[latest["indicator_name"] == indicator].dropna(subset=["iso3", "value"])
        if latest_ind.empty:
            continue
        fig = px.choropleth(
            latest_ind,
            locations="iso3",
            color="value",
            hover_name="country",
            color_continuous_scale="YlGnBu",
            projection="natural earth",
            title=f"{indicator}, {latest_year}",
            labels={"value": "Value"},
        )
        fig.update_geos(showframe=False, showcoastlines=True, landcolor="#f5f7fa")
        write_chart(
            fig,
            f"trade_map_{indicator.lower().split()[0]}_{latest_year}",
            f"Map: {indicator}, {latest_year}",
            sections,
        )

    yoy = plot_df.dropna(subset=["yoy_change_pct"])
    fig = px.box(
        yoy,
        x="period",
        y="yoy_change_pct",
        color="indicator_name",
        category_orders={"period": PERIOD_ORDER},
        title="YoY change distribution by trade-war period",
        labels={"yoy_change_pct": "YoY change (%)", "period": "", "indicator_name": "Indicator"},
    )
    write_chart(fig, "trade_yoy_by_period", "YoY changes by period", sections)
    close_section(sections)


def make_currency_charts(df: pd.DataFrame, sections: list[str]) -> None:
    add_section(
        sections,
        "5. Currency Impact",
        "<p>Exchange rates versus USD, rolling volatility, and changes around tariff events.</p>",
    )
    fig = px.line(
        df,
        x="date",
        y="rate_vs_usd",
        color="currency",
        title="Exchange rates versus USD",
        labels={"date": "", "rate_vs_usd": "Currency units per USD", "currency": "Currency"},
    )
    write_chart(fig, "currency_rate_trends", "Exchange-rate trends", sections)

    fig = px.line(
        df,
        x="date",
        y="rolling_7d_vol",
        color="currency",
        title="7-day rolling exchange-rate volatility",
        labels={"date": "", "rolling_7d_vol": "7-day volatility", "currency": "Currency"},
    )
    write_chart(fig, "currency_rolling_volatility", "Currency volatility trends", sections)

    fig = px.box(
        df.dropna(subset=["pct_change_1d"]),
        x="tariff_event_nearby",
        y="pct_change_1d",
        color="currency",
        title="One-day currency moves near tariff events",
        labels={"tariff_event_nearby": "Tariff event nearby", "pct_change_1d": "1-day change (%)"},
    )
    write_chart(fig, "currency_event_boxplot", "Currency moves near events", sections)

    latest = df.sort_values("date").groupby("currency", as_index=False).tail(1)
    fig = px.bar(
        latest.sort_values("pct_change_30d"),
        x="currency",
        y="pct_change_30d",
        color="country",
        title="Latest 30-day currency change",
        labels={"pct_change_30d": "30-day change (%)", "currency": "Currency"},
    )
    write_chart(fig, "currency_latest_30d_change", "Latest currency changes", sections)
    close_section(sections)


def make_sector_charts(df: pd.DataFrame, sections: list[str]) -> None:
    add_section(
        sections,
        "6. Sector Impact",
        "<p>ETF/sector performance by country, tariff sensitivity, returns, and volatility.</p>",
    )
    fig = px.line(
        df,
        x="date",
        y="indexed_to_100",
        color="sector",
        facet_col="country",
        facet_col_wrap=3,
        title="Sector performance indexed to 100",
        labels={"date": "", "indexed_to_100": "Index", "sector": "Sector"},
    )
    write_chart(fig, "sector_indexed_performance", "Sector performance", sections)

    latest = df.sort_values("date").groupby(["country", "sector"], as_index=False).tail(1)
    heat = latest.pivot_table(index="sector", columns="country", values="indexed_to_100", aggfunc="mean")
    fig = px.imshow(
        heat,
        aspect="auto",
        color_continuous_scale="RdYlGn",
        title="Latest sector performance by country",
        labels=dict(x="Country", y="Sector", color="Index"),
    )
    write_chart(fig, "sector_latest_heatmap", "Latest sector performance heatmap", sections)

    fig = px.violin(
        df.dropna(subset=["daily_return_pct"]),
        x="tariff_sensitivity",
        y="daily_return_pct",
        color="tariff_sensitivity",
        box=True,
        title="Daily return distribution by tariff sensitivity",
        labels={"daily_return_pct": "Daily return (%)", "tariff_sensitivity": "Tariff sensitivity"},
    )
    write_chart(fig, "sector_return_by_sensitivity", "Sector return distributions", sections)

    vol = latest.sort_values("volatility_10d", ascending=False)
    fig = px.bar(
        vol,
        x="volatility_10d",
        y="sector_label",
        color="country",
        orientation="h",
        title="Latest 10-day sector volatility",
        labels={"volatility_10d": "10-day volatility", "sector_label": ""},
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    write_chart(fig, "sector_latest_volatility", "Latest sector volatility", sections)
    close_section(sections)


def make_stock_charts(df: pd.DataFrame, sections: list[str]) -> None:
    add_section(
        sections,
        "7. Stock Market Reaction",
        "<p>Country index performance, volatility, returns, and tariff-event comparisons.</p>",
    )
    fig = px.line(
        df,
        x="date",
        y="indexed_to_100",
        color="index_name",
        title="Stock market indices indexed to 100",
        labels={"date": "", "indexed_to_100": "Index", "index_name": "Index"},
    )
    write_chart(fig, "stock_indexed_performance", "Stock-index performance", sections)

    fig = px.box(
        df.dropna(subset=["daily_return_pct"]),
        x="country",
        y="daily_return_pct",
        color="tariff_event_nearby",
        title="Daily stock returns by country and tariff-event proximity",
        labels={"daily_return_pct": "Daily return (%)", "country": "", "tariff_event_nearby": "Event nearby"},
    )
    write_chart(fig, "stock_daily_returns_event_boxplot", "Stock returns around tariff events", sections)

    latest = df.sort_values("date").groupby("country", as_index=False).tail(1)
    fig = px.bar(
        latest.sort_values("volatility_20d", ascending=False),
        x="volatility_20d",
        y="index_name",
        color="country",
        orientation="h",
        title="Latest 20-day stock-index volatility",
        labels={"volatility_20d": "20-day volatility", "index_name": ""},
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    write_chart(fig, "stock_latest_volatility", "Latest stock volatility", sections)

    returns = df.copy()
    returns["year"] = returns["date"].dt.year
    annual = returns.groupby(["country", "year"], as_index=False)["daily_return_pct"].mean()
    heat = annual.pivot_table(index="country", columns="year", values="daily_return_pct")
    fig = px.imshow(
        heat,
        aspect="auto",
        color_continuous_scale="RdBu",
        color_continuous_midpoint=0,
        title="Average daily stock return by year",
        labels=dict(x="Year", y="Country", color="Avg daily return %"),
    )
    write_chart(fig, "stock_annual_return_heatmap", "Annual stock-return heatmap", sections)
    close_section(sections)


def make_inflation_charts(df: pd.DataFrame, sections: list[str]) -> None:
    add_section(
        sections,
        "8. Inflation Response",
        "<p>Monthly CPI/PPI measures, year-over-year inflation, and era comparisons.</p>",
    )
    fig = px.line(
        df,
        x="date",
        y="value",
        color="country",
        facet_row="metric",
        title="Inflation index values by country",
        labels={"date": "", "value": "Index/value", "country": "Country", "metric": "Metric"},
    )
    fig.update_yaxes(matches=None)
    write_chart(fig, "inflation_value_trends", "Inflation value trends", sections)

    yoy = df.dropna(subset=["yoy_change_pct"])
    fig = px.line(
        yoy,
        x="date",
        y="yoy_change_pct",
        color="country",
        facet_row="metric",
        title="YoY inflation response by country",
        labels={"date": "", "yoy_change_pct": "YoY change (%)", "country": "Country", "metric": "Metric"},
    )
    fig.update_yaxes(matches=None)
    write_chart(fig, "inflation_yoy_trends", "YoY inflation trends", sections)

    fig = px.box(
        yoy,
        x="era",
        y="yoy_change_pct",
        color="metric",
        category_orders={"era": ERA_ORDER},
        title="YoY inflation distribution by era",
        labels={"era": "", "yoy_change_pct": "YoY change (%)", "metric": "Metric"},
    )
    write_chart(fig, "inflation_yoy_by_era", "Inflation by era", sections)

    avg = yoy.groupby(["country", "metric", "post_tariff_era"], as_index=False)["yoy_change_pct"].mean()
    fig = px.bar(
        avg,
        x="country",
        y="yoy_change_pct",
        color="post_tariff_era",
        facet_row="metric",
        barmode="group",
        title="Average YoY inflation before vs after tariff era",
        labels={"yoy_change_pct": "Avg YoY change (%)", "country": "", "post_tariff_era": "Post tariff era"},
    )
    fig.update_yaxes(matches=None)
    write_chart(fig, "inflation_pre_post_bar", "Pre/post tariff inflation comparison", sections)
    close_section(sections)


def make_chapter_mapping_md(overview: pd.DataFrame) -> str:
    largest = overview.iloc[0]
    overview_markdown = dataframe_to_markdown(overview)
    return f"""# EDA Summary for `new/` CSV Files

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Dataset Inventory

{overview_markdown}

## Key EDA Findings

- The folder contains seven CSV files covering tariff events, annual trade/macro indicators, currency rates, sector ETFs, stock indices, inflation, and column metadata.
- Largest table: `{largest['file']}` with {int(largest['rows']):,} rows.
- The analytical shape is mostly time-series plus event data: daily financial market data, monthly inflation data, annual macro/trade data, and discrete tariff announcements.
- The dashboard-ready columns are already documented in `column_metadata.csv`, which makes it a good source for labels, tooltips, and field descriptions.
- Several files include missing values in lagged/rolling fields, which is expected at the beginning of each time series.

## Applying the 9 Course Chapters

### Chapter 1: Overview of data visualization
Used for defining the project purpose: explain trade-war effects through tariffs, trade volumes, markets, currencies, sectors, and inflation. The charts support exploration and comparison rather than a single static conclusion.

### Chapter 2: Visual models and encoding
Nominal variables: country, currency, sector, tariff type, tariff sensitivity, period/era. Quantitative variables: values, returns, volatility, tariff rates, affected trade value. Encodings used: position for time/category, color for grouping or intensity, size for affected trade value, and heatmap color for matrix values.

### Chapter 3: Graphical perception
Used pre-attentive color differences in heatmaps and event/status colors. Magnitude estimation is supported through common axes in line/bar charts and color scales in heatmaps. Multiple encodings are used carefully: e.g. tariff timeline uses x-position, y-position, color, and bubble size.

### Chapter 4: Visualization for multi-dimensional data
Used the most heavily. Amounts: bars and choropleths. Distributions: histograms, boxplots, violins. Proportions: dataset coverage and event group comparisons. Relationships: tariff imposing-target heatmap and event proximity comparisons. Trends: line charts for annual, monthly, and daily time series.

### Chapter 5: Visualization for graphs
Only lightly applicable. The tariff event table can be interpreted as a directed relationship from imposing country to target country; the heatmap is used instead of a node-link graph to avoid clutter.

### Chapter 6: Principles of figure design
Applied proportional ink in bars and choropleths, avoided 3D, used titles and captions, used multi-panel/faceted views for dense time-series data, and used sequential/diverging color scales where appropriate.

### Chapter 7: Map visualization
Applicable to country-level trade indicators. The EDA report includes choropleth maps for latest-year exports/imports/trade share when ISO mappings are available.

### Chapter 8: Interactive visualization
The generated Plotly HTML report supports hover details, zooming, legend selection, and standalone chart inspection. These interactions support filtering and view transformation before building the final dashboard.

### Chapter 9: Storytelling with data
The suggested narrative is: tariff actions create policy shocks; trade and macro indicators show annual structural effects; markets/currencies/sectors show faster reactions; inflation gives downstream consumer/producer impact.

## Recommended Dashboard Tabs

1. Trade volume overview: annual country map, ranking table, regional bars, and country trends.
2. Tariff timeline: event timeline, affected sectors, retaliation, imposing-target relationship.
3. Market reaction: stock indices and sector impacts near tariff events.
4. Currency and inflation response: exchange-rate movements and CPI/PPI comparisons.
5. Methodology/data quality: source files, missingness, coverage, and metadata.
"""


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    columns = [str(col) for col in df.columns]
    rows = [[str(value) for value in row] for row in df.to_numpy()]
    widths = [
        max(len(columns[i]), *(len(row[i]) for row in rows)) if rows else len(columns[i])
        for i in range(len(columns))
    ]
    header = "| " + " | ".join(columns[i].ljust(widths[i]) for i in range(len(columns))) + " |"
    separator = "| " + " | ".join("-" * widths[i] for i in range(len(columns))) + " |"
    body = [
        "| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(columns))) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def write_report_html(sections: list[str]) -> None:
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EDA Report: new CSV Files</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      color: #20242a;
      background: #f5f7fa;
    }}
    header {{
      background: #ffffff;
      border-bottom: 1px solid #d9dee7;
      padding: 28px 36px 22px;
    }}
    header h1 {{
      margin: 0 0 8px;
      font-size: 30px;
    }}
    header p {{
      margin: 0;
      color: #667085;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    section {{
      background: #ffffff;
      border: 1px solid #d9dee7;
      border-radius: 8px;
      margin: 0 0 22px;
      padding: 22px;
    }}
    section h2 {{
      margin: 0 0 8px;
      font-size: 22px;
    }}
    .chart-card {{
      border-top: 1px solid #e6ebf1;
      padding-top: 18px;
      margin-top: 18px;
    }}
    .chart-card h3 {{
      margin: 0 0 4px;
      font-size: 17px;
    }}
    .chart-note, .chart-link {{
      color: #667085;
      font-size: 13px;
    }}
    .chart-link a {{
      color: #227c74;
    }}
    .summary-table {{
      border-collapse: collapse;
      width: 100%;
      margin-top: 16px;
      font-size: 13px;
    }}
    .summary-table th,
    .summary-table td {{
      border: 1px solid #d9dee7;
      padding: 7px 8px;
      text-align: left;
    }}
    .summary-table th {{
      background: #eef3f7;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Exploratory Data Analysis: <code>new/</code> CSV Files</h1>
    <p>Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Interactive charts use Plotly; hover, zoom, pan, and legend selection are enabled.</p>
  </header>
  <main>
    {''.join(sections)}
  </main>
</body>
</html>
"""
    (OUTPUT_DIR / "new_csv_eda_report.html").write_text(html, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    files = {
        "column_metadata.csv": load_csv("column_metadata.csv"),
        "tariff_timeline.csv": load_csv("tariff_timeline.csv", parse_dates=["date"]),
        "trade_volume_annual.csv": load_csv("trade_volume_annual.csv"),
        "currency_impact.csv": load_csv("currency_impact.csv", parse_dates=["date"]),
        "sector_impact.csv": load_csv("sector_impact.csv", parse_dates=["date"]),
        "stock_market_reaction.csv": load_csv("stock_market_reaction.csv", parse_dates=["date"]),
        "inflation_response.csv": load_csv("inflation_response.csv", parse_dates=["date"]),
    }

    sections: list[str] = []
    overview = make_overview(files, sections)
    make_column_metadata_charts(files["column_metadata.csv"], sections)
    make_tariff_charts(files["tariff_timeline.csv"], sections)
    make_trade_volume_charts(files["trade_volume_annual.csv"], sections)
    make_currency_charts(files["currency_impact.csv"], sections)
    make_sector_charts(files["sector_impact.csv"], sections)
    make_stock_charts(files["stock_market_reaction.csv"], sections)
    make_inflation_charts(files["inflation_response.csv"], sections)

    write_report_html(sections)
    (OUTPUT_DIR / "eda_summary.md").write_text(make_chapter_mapping_md(overview), encoding="utf-8")

    print(f"Wrote {OUTPUT_DIR / 'new_csv_eda_report.html'}")
    print(f"Wrote {OUTPUT_DIR / 'eda_summary.md'}")
    print(f"Wrote charts to {CHART_DIR}")


if __name__ == "__main__":
    main()
