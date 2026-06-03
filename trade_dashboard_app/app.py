from pathlib import Path
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DATA_PATH = APP_DIR.parent / "new" / "trade_volume_annual.csv"
TARIFF_PATH = APP_DIR.parent / "new" / "tariff_timeline.csv"
STOCK_PATH = APP_DIR.parent / "new" / "stock_market_reaction.csv"
CURRENCY_PATH = APP_DIR.parent / "new" / "currency_impact.csv"
SECTOR_PATH = APP_DIR.parent / "new" / "sector_impact.csv"
INFLATION_PATH = APP_DIR.parent / "new" / "inflation_response.csv"

EXPORTS = "Exports of goods & services (USD)"
IMPORTS = "Imports of goods & services (USD)"
TRADE_FLOW_TO_LABEL = {
    "Exports": EXPORTS,
    "Imports": IMPORTS,
    "Total trade": "Total trade (exports + imports)",
    "Trade balance": "Trade balance (exports - imports)",
}

COUNTRY_META = {
    "Australia": {"iso3": "AUS", "map_name": "Australia", "region": "Asia-Pacific"},
    "Brazil": {"iso3": "BRA", "map_name": "Brazil", "region": "Latin America"},
    "Canada": {"iso3": "CAN", "map_name": "Canada", "region": "North America"},
    "China": {"iso3": "CHN", "map_name": "China", "region": "Asia-Pacific"},
    "France": {"iso3": "FRA", "map_name": "France", "region": "Europe"},
    "Germany": {"iso3": "DEU", "map_name": "Germany", "region": "Europe"},
    "India": {"iso3": "IND", "map_name": "India", "region": "Asia-Pacific"},
    "Japan": {"iso3": "JPN", "map_name": "Japan", "region": "Asia-Pacific"},
    "Malaysia": {"iso3": "MYS", "map_name": "Malaysia", "region": "Asia-Pacific"},
    "Mexico": {"iso3": "MEX", "map_name": "Mexico", "region": "North America"},
    "Singapore": {"iso3": "SGP", "map_name": "Singapore", "region": "Asia-Pacific"},
    "South Korea": {"iso3": "KOR", "map_name": "South Korea", "region": "Asia-Pacific"},
    "UK": {"iso3": "GBR", "map_name": "United Kingdom", "region": "Europe"},
    "USA": {"iso3": "USA", "map_name": "United States", "region": "North America"},
    "Vietnam": {"iso3": "VNM", "map_name": "Vietnam", "region": "Asia-Pacific"},
}

PERIOD_ORDER = ["Pre-Trade War", "Trade War 1.0", "Recovery", "Trade War 2.0"]
PERIOD_COLORS = {
    "Pre-Trade War": "#5B8C7A",
    "Trade War 1.0": "#D9895B",
    "Recovery": "#4C78A8",
    "Trade War 2.0": "#B15C63",
}

ENTITY_META = {
    "USA": {"label": "United States", "iso3": "USA", "region": "North America"},
    "CHN": {"label": "China", "iso3": "CHN", "region": "Asia-Pacific"},
    "CAN": {"label": "Canada", "iso3": "CAN", "region": "North America"},
    "MEX": {"label": "Mexico", "iso3": "MEX", "region": "North America"},
    "IND": {"label": "India", "iso3": "IND", "region": "Asia-Pacific"},
    "JPN": {"label": "Japan", "iso3": "JPN", "region": "Asia-Pacific"},
    "GBR": {"label": "United Kingdom", "iso3": "GBR", "region": "Europe"},
    "EU27": {"label": "European Union", "iso3": None, "region": "Europe"},
    "GLOBAL": {"label": "Global / all partners", "iso3": None, "region": "Global"},
}

ENTITY_ALIASES = {
    "ALL": "GLOBAL",
    "GLOBAL": "GLOBAL",
    "USA": "USA",
    "US": "USA",
    "UNITED STATES": "USA",
    "CHN": "CHN",
    "CHINA": "CHN",
    "CAN": "CAN",
    "CANADA": "CAN",
    "MEX": "MEX",
    "MEXICO": "MEX",
    "IND": "IND",
    "INDIA": "IND",
    "JAPAN": "JPN",
    "JPN": "JPN",
    "UK": "GBR",
    "GBR": "GBR",
    "EU": "EU27",
    "EU27": "EU27",
}

TARIFF_TYPE_COLORS = {
    "New Tariff": "#227c74",
    "Escalation": "#b15c63",
    "Retaliation": "#d9895b",
    "Reduction": "#4c78a8",
    "Universal Baseline": "#7b61a8",
    "Expansion": "#8a8f36",
    "Export Control": "#6b7a8f",
    "Export Restriction": "#9467bd",
    "NewsAPI": "#8d99ae",
}

ERA_ORDER = ["Pre-Trade War", "Trade War 1.0", "Phase 1 + COVID", "Trade War 2.0"]


st.set_page_config(
    page_title="Global Trade Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
    :root {
        --ink: #20242a;
        --muted: #667085;
        --line: #d9dee7;
        --panel: #f7f9fb;
        --accent: #227c74;
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.4rem;
        max-width: 1260px;
    }
    h1, h2, h3 {
        color: var(--ink);
        letter-spacing: 0;
    }
    .page-title {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: flex-end;
        border-bottom: 1px solid var(--line);
        padding-bottom: 0.7rem;
        margin-bottom: 1rem;
    }
    .page-title h1 {
        margin: 0;
        font-size: 1.9rem;
        line-height: 1.2;
    }
    .page-title p {
        margin: 0.2rem 0 0;
        color: var(--muted);
        font-size: 0.95rem;
    }
    .source-note {
        color: var(--muted);
        font-size: 0.82rem;
        border-top: 1px solid var(--line);
        padding-top: 0.8rem;
        margin-top: 1.2rem;
    }
    div[data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 0.85rem 0.95rem;
    }
    div[data-testid="stMetricLabel"] {
        color: var(--muted);
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 6px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_trade_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["indicator_name"].isin([EXPORTS, IMPORTS])].copy()
    df["year"] = df["year"].astype(int)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["yoy_change_pct"] = pd.to_numeric(df["yoy_change_pct"], errors="coerce")
    df["iso3"] = df["country"].map(lambda c: COUNTRY_META.get(c, {}).get("iso3", c))
    df["map_name"] = df["country"].map(lambda c: COUNTRY_META.get(c, {}).get("map_name", c))
    df["region"] = df["country"].map(lambda c: COUNTRY_META.get(c, {}).get("region", "Other"))
    return df


def normalize_entity(value: str) -> str:
    key = str(value).strip().upper()
    return ENTITY_ALIASES.get(key, key)


def entity_label(code: str) -> str:
    return ENTITY_META.get(code, {}).get("label", code)


def entity_iso3(code: str):
    return ENTITY_META.get(code, {}).get("iso3")


@st.cache_data
def load_tariff_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["tariff_rate_pct", "prev_rate_pct", "estimated_trade_value_usd_bn", "tariff_rate_delta"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["imposing_norm"] = df["imposing_country"].map(normalize_entity)
    df["target_norm"] = df["target_country"].map(normalize_entity)
    df["imposing_label"] = df["imposing_norm"].map(entity_label)
    df["target_label"] = df["target_norm"].map(entity_label)
    df["imposing_iso3"] = df["imposing_norm"].map(entity_iso3)
    df["target_iso3"] = df["target_norm"].map(entity_iso3)
    df["imposing_region"] = df["imposing_norm"].map(lambda c: ENTITY_META.get(c, {}).get("region", "Other"))
    df["target_region"] = df["target_norm"].map(lambda c: ENTITY_META.get(c, {}).get("region", "Other"))
    df["retaliation_label"] = df["retaliation"].map({True: "Retaliation", False: "Initial or policy action"})
    df["trade_value_known"] = df["estimated_trade_value_usd_bn"].notna()
    df["trade_value_for_size"] = df["estimated_trade_value_usd_bn"].fillna(0).clip(lower=1)
    df["known_trade_value"] = df["estimated_trade_value_usd_bn"].fillna(0)
    return df


@st.cache_data
def load_stock_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    numeric_cols = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "daily_return_pct",
        "weekly_return_pct",
        "ma_20d",
        "ma_50d",
        "volatility_20d",
        "indexed_to_100",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_currency_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    numeric_cols = [
        "rate_vs_usd",
        "pct_change_1d",
        "pct_change_7d",
        "pct_change_30d",
        "rolling_30d_avg",
        "rolling_7d_vol",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_sector_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    numeric_cols = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "daily_return_pct",
        "weekly_return_pct",
        "indexed_to_100",
        "volatility_10d",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_inflation_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["value", "mom_change_pct", "yoy_change_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_macro_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["yoy_change_pct"] = pd.to_numeric(df["yoy_change_pct"], errors="coerce")
    return df


def prepare_trade_matrix(df: pd.DataFrame) -> pd.DataFrame:
    index_cols = ["year", "country", "country_code", "iso3", "map_name", "region", "period"]
    wide = (
        df.pivot_table(
            index=index_cols,
            columns="indicator_name",
            values="value",
            aggfunc="sum",
        )
        .reset_index()
        .rename_axis(columns=None)
    )
    for col in [EXPORTS, IMPORTS]:
        if col not in wide:
            wide[col] = pd.NA
    wide[TRADE_FLOW_TO_LABEL["Total trade"]] = wide[[EXPORTS, IMPORTS]].sum(axis=1, min_count=1)
    wide[TRADE_FLOW_TO_LABEL["Trade balance"]] = wide[EXPORTS] - wide[IMPORTS]
    return wide


def format_usd(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000_000_000:
        return f"{sign}${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"{sign}${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:.1f}M"
    return f"{sign}${value:,.0f}"


def format_pct(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:+.1f}%"


def selected_metric_frame(wide: pd.DataFrame, year: int, metric_col: str) -> pd.DataFrame:
    year_df = wide[wide["year"] == year].copy()
    year_df = year_df.dropna(subset=[metric_col])
    year_df["metric_value"] = year_df[metric_col]
    year_df["rank"] = year_df["metric_value"].rank(method="first", ascending=False).astype(int)
    total = year_df["metric_value"].sum()
    year_df["dataset_share_pct"] = year_df["metric_value"] / total * 100 if total else pd.NA
    return year_df.sort_values("metric_value", ascending=False)


def compute_yoy(wide: pd.DataFrame, metric_col: str, year: int) -> pd.Series:
    metric = wide[["year", "country", metric_col]].dropna()
    metric = metric.sort_values(["country", "year"])
    metric["yoy"] = metric.groupby("country")[metric_col].pct_change() * 100
    return metric[metric["year"] == year].set_index("country")["yoy"]


def make_map(year_df: pd.DataFrame, trade_flow: str, year: int) -> go.Figure:
    positive_df = year_df.copy()
    if trade_flow == "Trade balance":
        color_scale = "RdBu"
        color_midpoint = 0
        color_title = "USD"
    else:
        color_scale = "YlGnBu"
        color_midpoint = None
        color_title = "USD"

    fig = px.choropleth(
        positive_df,
        locations="iso3",
        color="metric_value",
        hover_name="country",
        hover_data={
            "iso3": False,
            "region": True,
            "metric_value": ":,.0f",
            "dataset_share_pct": ":.2f",
        },
        color_continuous_scale=color_scale,
        color_continuous_midpoint=color_midpoint,
        projection="natural earth",
        labels={"metric_value": color_title, "dataset_share_pct": "Dataset share %"},
        title=f"Goods & services, {trade_flow}, {year}",
    )
    fig.update_geos(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#b6c1c9",
        showland=True,
        landcolor="#f2f4f7",
        showcountries=True,
        countrycolor="#ffffff",
        bgcolor="#ffffff",
    )
    fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=56, b=0),
        title=dict(font=dict(size=22), x=0.5),
        coloraxis_colorbar=dict(title=color_title, ticks="outside"),
    )
    return fig


def make_regional_bar(year_df: pd.DataFrame, trade_flow: str) -> go.Figure:
    plot_df = year_df.sort_values(["region", "metric_value"], ascending=[True, False])
    fig = px.bar(
        plot_df,
        x="region",
        y="metric_value",
        color="country",
        custom_data=["country", "dataset_share_pct"],
        title=f"Regional composition of {trade_flow.lower()}",
        labels={"region": "", "metric_value": "US dollars", "country": "Country"},
    )
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>Value: $%{y:,.0f}<br>Share: %{customdata[1]:.2f}%<extra></extra>"
    )
    fig.update_layout(
        barmode="stack",
        height=430,
        margin=dict(l=0, r=0, t=48, b=0),
        legend=dict(orientation="h", y=-0.25, x=0),
        yaxis=dict(tickformat="~s", gridcolor="#e9edf3"),
        xaxis=dict(tickangle=0),
    )
    return fig


def make_country_trend(wide: pd.DataFrame, selected_country: str) -> go.Figure:
    country_df = wide[wide["country"] == selected_country].sort_values("year")
    fig = go.Figure()
    traces = [
        (EXPORTS, "Exports", "#227c74"),
        (IMPORTS, "Imports", "#4C78A8"),
        (TRADE_FLOW_TO_LABEL["Trade balance"], "Trade balance", "#D9895B"),
    ]
    for col, label, color in traces:
        if col in country_df and country_df[col].notna().any():
            fig.add_trace(
                go.Scatter(
                    x=country_df["year"],
                    y=country_df[col],
                    mode="lines+markers",
                    name=label,
                    line=dict(color=color, width=3),
                    marker=dict(size=7),
                    hovertemplate=f"{label}<br>%{{x}}: $%{{y:,.0f}}<extra></extra>",
                )
            )
    fig.update_layout(
        title=f"{selected_country}, annual trade values",
        height=360,
        margin=dict(l=0, r=0, t=48, b=0),
        yaxis=dict(title="US dollars", tickformat="~s", gridcolor="#e9edf3"),
        xaxis=dict(title="", dtick=1),
        legend=dict(orientation="h", y=-0.25, x=0),
    )
    return fig


def make_aggregate_trend(wide: pd.DataFrame) -> go.Figure:
    agg = (
        wide.groupby(["year", "period"], as_index=False)[[EXPORTS, IMPORTS]]
        .sum(min_count=1)
        .sort_values("year")
    )
    fig = go.Figure()
    for col, label, color in [(EXPORTS, "Exports", "#227c74"), (IMPORTS, "Imports", "#4C78A8")]:
        fig.add_trace(
            go.Scatter(
                x=agg["year"],
                y=agg[col],
                mode="lines+markers",
                name=label,
                line=dict(color=color, width=3),
                marker=dict(size=7),
                hovertemplate=f"{label}<br>%{{x}}: $%{{y:,.0f}}<extra></extra>",
            )
        )
    for period, group in agg.groupby("period"):
        if period in PERIOD_COLORS:
            fig.add_vrect(
                x0=group["year"].min() - 0.5,
                x1=group["year"].max() + 0.5,
                fillcolor=PERIOD_COLORS[period],
                opacity=0.08,
                layer="below",
                line_width=0,
            )
    fig.update_layout(
        title="Dataset aggregate, exports and imports",
        height=360,
        margin=dict(l=0, r=0, t=48, b=0),
        yaxis=dict(title="US dollars", tickformat="~s", gridcolor="#e9edf3"),
        xaxis=dict(title="", dtick=1),
        legend=dict(orientation="h", y=-0.25, x=0),
    )
    return fig


def make_index_chart(wide: pd.DataFrame, trade_flow: str, metric_col: str, base_year: int) -> go.Figure:
    agg = (
        wide.groupby(["year", "period"], as_index=False)[metric_col]
        .sum(min_count=1)
        .dropna(subset=[metric_col])
        .sort_values("year")
    )
    base = agg.loc[agg["year"] == base_year, metric_col]
    if base.empty or base.iloc[0] == 0:
        agg["index"] = pd.NA
    else:
        agg["index"] = agg[metric_col] / base.iloc[0] * 100
    fig = px.bar(
        agg,
        x="year",
        y="index",
        color="period",
        color_discrete_map=PERIOD_COLORS,
        category_orders={"period": PERIOD_ORDER},
        title=f"Dataset aggregate index, {trade_flow} ({base_year} = 100)",
        labels={"year": "", "index": "Index", "period": "Period"},
    )
    fig.update_traces(hovertemplate="%{x}<br>Index: %{y:.1f}<extra></extra>")
    fig.update_layout(
        height=340,
        margin=dict(l=0, r=0, t=48, b=0),
        yaxis=dict(range=[0, max(130, agg["index"].max() * 1.12)], gridcolor="#e9edf3"),
        xaxis=dict(dtick=1),
        legend=dict(orientation="h", y=-0.24, x=0),
    )
    return fig


def tariff_weight_column(weight_mode: str) -> str:
    return "known_trade_value" if weight_mode == "Estimated trade value" else "event_count"


def aggregate_tariff_edges(df: pd.DataFrame, weight_mode: str) -> pd.DataFrame:
    edge_df = df.copy()
    edge_df["event_count"] = 1
    weight_col = tariff_weight_column(weight_mode)
    edges = (
        edge_df.groupby(["imposing_norm", "target_norm", "imposing_label", "target_label"], as_index=False)
        .agg(
            event_count=("event_count", "sum"),
            known_trade_value=("known_trade_value", "sum"),
            avg_rate=("tariff_rate_pct", "mean"),
            latest_date=("date", "max"),
        )
    )
    edges["weight"] = edges[weight_col]
    if weight_mode == "Estimated trade value":
        edges = edges[edges["weight"] > 0]
    return edges.sort_values("weight", ascending=False)


def make_tariff_cumulative_chart(df: pd.DataFrame) -> go.Figure:
    daily = (
        df.sort_values("date")
        .groupby("date", as_index=False)
        .agg(events=("type", "count"), known_trade_value=("known_trade_value", "sum"))
    )
    daily["cumulative_events"] = daily["events"].cumsum()
    daily["cumulative_trade_value"] = daily["known_trade_value"].cumsum()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["cumulative_events"],
            mode="lines+markers",
            name="Cumulative events",
            line=dict(color="#227c74", width=3),
            hovertemplate="%{x|%Y-%m-%d}<br>Events: %{y:,}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["cumulative_trade_value"],
            mode="lines+markers",
            name="Known affected trade value",
            yaxis="y2",
            line=dict(color="#b15c63", width=3),
            hovertemplate="%{x|%Y-%m-%d}<br>USD bn: %{y:,.1f}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Cumulative tariff pressure",
        height=360,
        margin=dict(l=0, r=0, t=48, b=0),
        yaxis=dict(title="Events", gridcolor="#e9edf3"),
        yaxis2=dict(title="USD billions", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=-0.24, x=0),
    )
    return fig


def make_tariff_actions_by_year(df: pd.DataFrame) -> go.Figure:
    counts = df.groupby(["year", "type"], as_index=False).size()
    fig = px.bar(
        counts,
        x="year",
        y="size",
        color="type",
        color_discrete_map=TARIFF_TYPE_COLORS,
        title="Actions by year and type",
        labels={"year": "", "size": "Events", "type": "Action type"},
    )
    fig.update_layout(height=360, legend=dict(orientation="h", y=-0.28, x=0), yaxis=dict(gridcolor="#e9edf3"))
    return fig


def make_tariff_rate_distribution(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        df,
        x="tariff_rate_delta",
        color="retaliation_label",
        nbins=24,
        marginal="rug",
        title="Distribution of tariff-rate changes",
        labels={"tariff_rate_delta": "Rate change (%)", "retaliation_label": ""},
        color_discrete_map={"Retaliation": "#d9895b", "Initial or policy action": "#4c78a8"},
    )
    fig.update_layout(height=360, yaxis=dict(gridcolor="#e9edf3"))
    return fig


def make_tariff_sector_bar(df: pd.DataFrame, weight_mode: str) -> go.Figure:
    work = df.copy()
    work["event_count"] = 1
    weight_col = tariff_weight_column(weight_mode)
    sectors = (
        work.groupby("sector", as_index=False)[weight_col]
        .sum()
        .sort_values(weight_col, ascending=False)
        .head(18)
    )
    fig = px.bar(
        sectors,
        x=weight_col,
        y="sector",
        orientation="h",
        title=f"Top sectors by {weight_mode.lower()}",
        labels={weight_col: "USD billions" if weight_mode == "Estimated trade value" else "Events", "sector": ""},
        color=weight_col,
        color_continuous_scale="Teal",
    )
    fig.update_layout(height=520, yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
    return fig


def make_tariff_type_treemap(df: pd.DataFrame) -> go.Figure:
    work = df.copy()
    work["event_count"] = 1
    fig = px.treemap(
        work,
        path=["type", "retaliation_label", "imposing_label"],
        values="event_count",
        color="tariff_rate_pct",
        color_continuous_scale="YlOrRd",
        title="Action mix by type, retaliation status, and imposing economy",
        labels={"tariff_rate_pct": "Avg tariff rate (%)"},
    )
    fig.update_layout(height=500)
    return fig


def make_tariff_network(df: pd.DataFrame, weight_mode: str) -> go.Figure:
    edges = aggregate_tariff_edges(df, weight_mode).head(35)
    if edges.empty:
        return go.Figure().update_layout(title="No known trade-value edges for current filters", height=560)

    node_codes = sorted(set(edges["imposing_norm"]) | set(edges["target_norm"]))
    node_labels = {code: entity_label(code) for code in node_codes}
    n = len(node_codes)
    weighted_degree = {}
    out_weight = {}
    in_weight = {}
    for code in node_codes:
        out_weight[code] = edges.loc[edges["imposing_norm"] == code, "weight"].sum()
        in_weight[code] = edges.loc[edges["target_norm"] == code, "weight"].sum()
        weighted_degree[code] = out_weight[code] + in_weight[code]

    ordered = sorted(node_codes, key=lambda c: weighted_degree[c], reverse=True)
    positions = {}
    for i, code in enumerate(ordered):
        angle = 2 * math.pi * i / max(n, 1)
        positions[code] = (math.cos(angle), math.sin(angle))

    max_edge = max(edges["weight"].max(), 1)
    fig = go.Figure()
    annotations = []
    for row in edges.itertuples():
        x0, y0 = positions[row.imposing_norm]
        x1, y1 = positions[row.target_norm]
        width = 1 + 5 * (row.weight / max_edge) ** 0.5
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(width=width, color="rgba(94, 112, 125, 0.34)"),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        annotations.append(
            dict(
                x=x1,
                y=y1,
                ax=x0,
                ay=y0,
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                showarrow=True,
                arrowhead=3,
                arrowsize=1,
                arrowwidth=max(1, width * 0.65),
                arrowcolor="rgba(177, 92, 99, 0.50)",
                opacity=0.78,
            )
        )

    max_degree = max(weighted_degree.values()) if weighted_degree else 1
    node_x = [positions[code][0] for code in ordered]
    node_y = [positions[code][1] for code in ordered]
    node_sizes = [20 + 42 * (weighted_degree[code] / max_degree) ** 0.5 for code in ordered]
    net_out = [out_weight[code] - in_weight[code] for code in ordered]
    hover = [
        f"<b>{node_labels[code]}</b><br>"
        f"Outgoing: {out_weight[code]:,.1f}<br>"
        f"Incoming: {in_weight[code]:,.1f}<br>"
        f"Total: {weighted_degree[code]:,.1f}"
        for code in ordered
    ]
    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=[node_labels[code] for code in ordered],
            textposition="bottom center",
            marker=dict(
                size=node_sizes,
                color=net_out,
                colorscale="RdBu",
                reversescale=True,
                cmid=0,
                line=dict(width=1.5, color="#ffffff"),
                colorbar=dict(title="Net outgoing"),
            ),
            hovertext=hover,
            hoverinfo="text",
            showlegend=False,
        )
    )
    fig.update_layout(
        title=f"Directed tariff network by {weight_mode.lower()}",
        height=590,
        annotations=annotations,
        xaxis=dict(visible=False, range=[-1.35, 1.35]),
        yaxis=dict(visible=False, range=[-1.28, 1.28]),
        margin=dict(l=0, r=0, t=52, b=0),
        plot_bgcolor="#ffffff",
    )
    return fig


def make_tariff_country_map(df: pd.DataFrame, role: str, weight_mode: str) -> go.Figure:
    work = df.copy()
    work["event_count"] = 1
    code_col = f"{role}_norm"
    label_col = f"{role}_label"
    iso_col = f"{role}_iso3"
    weight_col = tariff_weight_column(weight_mode)
    agg = (
        work.dropna(subset=[iso_col])
        .groupby([code_col, label_col, iso_col], as_index=False)
        .agg(weight=(weight_col, "sum"), avg_rate=("tariff_rate_pct", "mean"), events=("type", "count"))
    )
    title_role = "imposing economies" if role == "imposing" else "target economies"
    if agg.empty:
        return go.Figure().update_layout(title=f"No mappable {title_role} for current filters", height=430)
    fig = px.choropleth(
        agg,
        locations=iso_col,
        color="weight",
        hover_name=label_col,
        hover_data={"events": True, "avg_rate": ":.1f", "weight": ":,.1f", iso_col: False},
        color_continuous_scale="YlOrRd",
        projection="natural earth",
        title=f"Map of {title_role} by {weight_mode.lower()}",
        labels={"weight": "USD bn" if weight_mode == "Estimated trade value" else "Events", "avg_rate": "Avg rate %"},
    )
    fig.update_geos(showframe=False, showcoastlines=True, landcolor="#f5f7fa", countrycolor="#ffffff")
    fig.update_layout(height=430, margin=dict(l=0, r=0, t=52, b=0))
    return fig


def make_tariff_source_chart(df: pd.DataFrame) -> go.Figure:
    source = df.groupby("source", as_index=False).size().sort_values("size", ascending=False).head(14)
    fig = px.bar(
        source,
        x="size",
        y="source",
        orientation="h",
        title="Top sources in the tariff timeline",
        labels={"size": "Events", "source": ""},
        color="size",
        color_continuous_scale="Blues",
    )
    fig.update_layout(height=430, yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
    return fig


def make_tariff_rate_value_scatter(df: pd.DataFrame) -> go.Figure:
    known = df.dropna(subset=["estimated_trade_value_usd_bn"])
    fig = px.scatter(
        known,
        x="estimated_trade_value_usd_bn",
        y="tariff_rate_pct",
        color="type",
        size="trade_value_for_size",
        color_discrete_map=TARIFF_TYPE_COLORS,
        hover_name="sector",
        hover_data=["imposing_label", "target_label", "date", "notes"],
        title="Tariff rate vs known affected trade value",
        labels={"estimated_trade_value_usd_bn": "Affected trade value (USD bn)", "tariff_rate_pct": "Tariff rate (%)"},
    )
    fig.update_layout(height=430, xaxis=dict(gridcolor="#e9edf3"), yaxis=dict(gridcolor="#e9edf3"))
    return fig


def filter_by_date(df: pd.DataFrame, key_prefix: str):
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    selected = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key=f"{key_prefix}_date_range",
    )
    if isinstance(selected, tuple) and len(selected) == 2:
        start_date, end_date = pd.to_datetime(selected[0]), pd.to_datetime(selected[1])
    else:
        start_date, end_date = pd.to_datetime(min_date), pd.to_datetime(max_date)
    return df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()


def make_latest_table(df: pd.DataFrame, group_cols: list[str], date_col: str = "date") -> pd.DataFrame:
    return df.sort_values(date_col).groupby(group_cols, as_index=False).tail(1)


def make_market_performance_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df,
        x="date",
        y="indexed_to_100",
        color="index_name",
        title="Market performance indexed to 100",
        labels={"date": "", "indexed_to_100": "Index", "index_name": "Market index"},
    )
    fig.update_layout(height=460, legend=dict(orientation="h", y=-0.28, x=0), yaxis=dict(gridcolor="#e9edf3"))
    return fig


def make_market_event_box(df: pd.DataFrame) -> go.Figure:
    fig = px.box(
        df.dropna(subset=["daily_return_pct"]),
        x="tariff_event_nearby",
        y="daily_return_pct",
        color="country",
        title="Daily returns near tariff events",
        labels={"tariff_event_nearby": "Tariff event nearby", "daily_return_pct": "Daily return (%)", "country": "Country"},
    )
    fig.update_layout(height=420, legend=dict(orientation="h", y=-0.30, x=0), yaxis=dict(gridcolor="#e9edf3"))
    return fig


def make_market_latest_bar(df: pd.DataFrame) -> go.Figure:
    latest = make_latest_table(df, ["country", "index_name"]).sort_values("indexed_to_100", ascending=False)
    fig = px.bar(
        latest,
        x="indexed_to_100",
        y="index_name",
        color="country",
        orientation="h",
        title="Latest market performance",
        labels={"indexed_to_100": "Index", "index_name": ""},
    )
    fig.update_layout(height=500, yaxis=dict(autorange="reversed"), xaxis=dict(gridcolor="#e9edf3"))
    return fig


def make_market_volatility_chart(df: pd.DataFrame) -> go.Figure:
    latest = make_latest_table(df, ["country", "index_name"]).sort_values("volatility_20d", ascending=False)
    fig = px.bar(
        latest,
        x="volatility_20d",
        y="index_name",
        color="country",
        orientation="h",
        title="Latest 20-day volatility",
        labels={"volatility_20d": "20-day volatility", "index_name": ""},
    )
    fig.update_layout(height=500, yaxis=dict(autorange="reversed"), xaxis=dict(gridcolor="#e9edf3"))
    return fig


def make_market_annual_heatmap(df: pd.DataFrame) -> go.Figure:
    work = df.dropna(subset=["daily_return_pct"]).copy()
    work["year"] = work["date"].dt.year
    matrix = work.pivot_table(index="country", columns="year", values="daily_return_pct", aggfunc="mean")
    fig = px.imshow(
        matrix,
        aspect="auto",
        color_continuous_scale="RdBu",
        color_continuous_midpoint=0,
        title="Average daily return by year",
        labels={"x": "Year", "y": "Country", "color": "Avg daily return %"},
    )
    fig.update_layout(height=430)
    return fig


def make_currency_rate_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df,
        x="date",
        y="rate_vs_usd",
        color="currency",
        title="Exchange rates versus USD",
        labels={"date": "", "rate_vs_usd": "Currency units per USD", "currency": "Currency"},
    )
    fig.update_layout(height=460, legend=dict(orientation="h", y=-0.26, x=0), yaxis=dict(gridcolor="#e9edf3"))
    return fig


def make_currency_volatility_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df,
        x="date",
        y="rolling_7d_vol",
        color="currency",
        title="7-day exchange-rate volatility",
        labels={"date": "", "rolling_7d_vol": "7-day volatility", "currency": "Currency"},
    )
    fig.update_layout(height=420, legend=dict(orientation="h", y=-0.28, x=0), yaxis=dict(gridcolor="#e9edf3"))
    return fig


def make_currency_event_box(df: pd.DataFrame) -> go.Figure:
    fig = px.box(
        df.dropna(subset=["pct_change_1d"]),
        x="tariff_event_nearby",
        y="pct_change_1d",
        color="currency",
        title="One-day currency moves near tariff events",
        labels={"tariff_event_nearby": "Tariff event nearby", "pct_change_1d": "1-day change (%)"},
    )
    fig.update_layout(height=420, legend=dict(orientation="h", y=-0.28, x=0), yaxis=dict(gridcolor="#e9edf3"))
    return fig


def make_currency_latest_pressure(df: pd.DataFrame) -> go.Figure:
    latest = make_latest_table(df, ["currency", "country"]).sort_values("pct_change_30d", ascending=False)
    fig = px.bar(
        latest,
        x="currency",
        y="pct_change_30d",
        color="country",
        title="Latest 30-day exchange-rate pressure",
        labels={"currency": "", "pct_change_30d": "30-day change (%)"},
    )
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="#667085")
    fig.update_layout(height=420, yaxis=dict(gridcolor="#e9edf3"), legend=dict(orientation="h", y=-0.28, x=0))
    return fig


def make_currency_change_heatmap(df: pd.DataFrame) -> go.Figure:
    work = df.dropna(subset=["pct_change_30d"]).copy()
    work["year"] = work["date"].dt.year
    matrix = work.pivot_table(index="currency", columns="year", values="pct_change_30d", aggfunc="mean")
    fig = px.imshow(
        matrix,
        aspect="auto",
        color_continuous_scale="RdBu",
        color_continuous_midpoint=0,
        title="Average 30-day currency change by year",
        labels={"x": "Year", "y": "Currency", "color": "Avg 30-day change %"},
    )
    fig.update_layout(height=430)
    return fig


def make_sector_performance_chart(df: pd.DataFrame) -> go.Figure:
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
    fig.update_layout(height=560, legend=dict(orientation="h", y=-0.22, x=0))
    fig.update_yaxes(matches=None, gridcolor="#e9edf3")
    return fig


def make_sector_latest_heatmap(df: pd.DataFrame) -> go.Figure:
    latest = make_latest_table(df, ["country", "sector"])
    matrix = latest.pivot_table(index="sector", columns="country", values="indexed_to_100", aggfunc="mean")
    fig = px.imshow(
        matrix,
        aspect="auto",
        color_continuous_scale="RdYlGn",
        title="Latest sector performance by country",
        labels={"x": "Country", "y": "Sector", "color": "Index"},
    )
    fig.update_layout(height=500)
    return fig


def make_sector_return_distribution(df: pd.DataFrame) -> go.Figure:
    fig = px.violin(
        df.dropna(subset=["daily_return_pct"]),
        x="tariff_sensitivity",
        y="daily_return_pct",
        color="tariff_sensitivity",
        box=True,
        title="Daily return distribution by tariff sensitivity",
        labels={"tariff_sensitivity": "Tariff sensitivity", "daily_return_pct": "Daily return (%)"},
    )
    fig.update_layout(height=430, yaxis=dict(gridcolor="#e9edf3"))
    return fig


def make_sector_volatility_bar(df: pd.DataFrame) -> go.Figure:
    latest = make_latest_table(df, ["country", "sector"]).sort_values("volatility_10d", ascending=False).head(24)
    fig = px.bar(
        latest,
        x="volatility_10d",
        y="sector_label",
        color="country",
        orientation="h",
        title="Latest sector volatility",
        labels={"volatility_10d": "10-day volatility", "sector_label": ""},
    )
    fig.update_layout(height=520, yaxis=dict(autorange="reversed"), xaxis=dict(gridcolor="#e9edf3"))
    return fig


def make_vietnam_trade_chart(macro: pd.DataFrame) -> go.Figure:
    vn = macro[macro["country"] == "Vietnam"].copy()
    keep = [
        "Exports of goods & services (USD)",
        "Imports of goods & services (USD)",
        "GDP (current USD)",
        "Trade (% of GDP)",
        "GDP growth (annual %)",
        "CPI inflation (annual %)",
    ]
    vn = vn[vn["indicator_name"].isin(keep)]
    fig = px.line(
        vn,
        x="year",
        y="value",
        color="indicator_name",
        facet_row="indicator_name",
        title="Vietnam annual trade and macro indicators",
        labels={"year": "", "value": "Value", "indicator_name": ""},
    )
    fig.update_yaxes(matches=None, tickformat="~s")
    fig.update_layout(height=720, showlegend=False)
    return fig


def make_vietnam_market_currency_chart(stock: pd.DataFrame, currency: pd.DataFrame) -> go.Figure:
    vn_stock = stock[stock["country"] == "Vietnam"].copy()
    vn_currency = currency[currency["country"] == "Vietnam"].copy()
    fig = go.Figure()
    if not vn_stock.empty:
        fig.add_trace(
            go.Scatter(
                x=vn_stock["date"],
                y=vn_stock["indexed_to_100"],
                mode="lines",
                name="VN-Index (indexed)",
                line=dict(color="#227c74", width=2.4),
            )
        )
    if not vn_currency.empty:
        first = vn_currency["rate_vs_usd"].dropna().iloc[0]
        vn_currency["vnd_index"] = vn_currency["rate_vs_usd"] / first * 100
        fig.add_trace(
            go.Scatter(
                x=vn_currency["date"],
                y=vn_currency["vnd_index"],
                mode="lines",
                name="VND per USD (indexed)",
                line=dict(color="#b15c63", width=2.4),
            )
        )
    fig.update_layout(
        title="Vietnam financial pressure: VN-Index and VND per USD",
        height=430,
        yaxis=dict(title="Index, start = 100", gridcolor="#e9edf3"),
        xaxis=dict(title=""),
        legend=dict(orientation="h", y=-0.22, x=0),
    )
    return fig


def make_macro_indicator_chart(df: pd.DataFrame, countries: list[str], indicators: list[str]) -> go.Figure:
    work = df[df["country"].isin(countries) & df["indicator_name"].isin(indicators)].copy()
    fig = px.line(
        work,
        x="year",
        y="value",
        color="country",
        facet_row="indicator_name",
        title="Long-term macro indicators",
        labels={"year": "", "value": "Value", "country": "Country", "indicator_name": ""},
    )
    fig.update_yaxes(matches=None, tickformat="~s")
    fig.update_layout(height=max(420, 170 * len(indicators)), legend=dict(orientation="h", y=-0.12, x=0))
    return fig


def make_macro_period_box(df: pd.DataFrame, indicator: str) -> go.Figure:
    work = df[df["indicator_name"] == indicator].dropna(subset=["yoy_change_pct"]).copy()
    fig = px.box(
        work,
        x="period",
        y="yoy_change_pct",
        color="period",
        category_orders={"period": PERIOD_ORDER},
        color_discrete_map=PERIOD_COLORS,
        title=f"YoY distribution by period: {indicator}",
        labels={"period": "", "yoy_change_pct": "YoY change (%)"},
    )
    fig.update_layout(height=420, yaxis=dict(gridcolor="#e9edf3"), showlegend=False)
    return fig


def make_macro_latest_heatmap(df: pd.DataFrame, indicators: list[str]) -> go.Figure:
    latest_year = int(df["year"].max())
    latest = df[(df["year"] == latest_year) & df["indicator_name"].isin(indicators)].copy()
    matrix = latest.pivot_table(index="country", columns="indicator_name", values="value", aggfunc="mean")
    fig = px.imshow(
        matrix,
        aspect="auto",
        color_continuous_scale="YlGnBu",
        title=f"Latest macro values, {latest_year}",
        labels={"x": "Indicator", "y": "Country", "color": "Value"},
    )
    fig.update_layout(height=520)
    return fig


def make_macro_correlation_heatmap(df: pd.DataFrame, indicators: list[str]) -> go.Figure:
    work = df[df["indicator_name"].isin(indicators)].copy()
    wide = work.pivot_table(index=["country", "year"], columns="indicator_name", values="value", aggfunc="mean")
    corr = wide.corr(numeric_only=True)
    fig = px.imshow(
        corr,
        color_continuous_scale="RdBu",
        color_continuous_midpoint=0,
        title="Indicator correlation across country-years",
        labels={"x": "Indicator", "y": "Indicator", "color": "Correlation"},
    )
    fig.update_layout(height=520)
    return fig


def make_usa_adjustment_chart(inflation: pd.DataFrame, metrics: list[str]) -> go.Figure:
    work = inflation[inflation["metric"].isin(metrics)].copy()
    fig = px.line(
        work,
        x="date",
        y="value",
        color="metric",
        facet_row="metric",
        title="US long-term adjustment indicators",
        labels={"date": "", "value": "Value", "metric": ""},
    )
    fig.update_yaxes(matches=None)
    fig.update_layout(height=max(420, 160 * len(metrics)), showlegend=False)
    return fig


def render_trade_volume_tab() -> None:
    raw = load_trade_data(DATA_PATH)
    wide = prepare_trade_matrix(raw)
    years = sorted(wide["year"].dropna().unique().tolist())
    max_year = max(years)

    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Trade Volume Dashboard</h1>
                <p>Annual goods and services trade, adapted from the WTO merchandise dashboard layout.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns([1.25, 1.0, 0.85, 1.15])
    with c1:
        indicator = st.selectbox(
            "Indicator",
            ["Goods & services trade"],
            index=0,
        )
    with c2:
        trade_flow = st.selectbox(
            "Trade Flow",
            list(TRADE_FLOW_TO_LABEL.keys()),
            index=0,
        )
    with c3:
        year = st.selectbox("Year", years, index=years.index(max_year))
    with c4:
        country_options = sorted(wide["country"].unique())
        selected_country = st.selectbox(
            "Economy",
            country_options,
            index=country_options.index("China") if "China" in country_options else 0,
        )

    metric_col = TRADE_FLOW_TO_LABEL[trade_flow]
    year_df = selected_metric_frame(wide, year, metric_col)
    yoy = compute_yoy(wide, metric_col, year)
    year_df["yoy_change_pct"] = year_df["country"].map(yoy)

    total_value = year_df["metric_value"].sum()
    avg_yoy = year_df["yoy_change_pct"].mean()
    top_row = year_df.iloc[0] if not year_df.empty else None
    previous_total = selected_metric_frame(wide, year - 1, metric_col)["metric_value"].sum() if year - 1 in years else pd.NA
    if pd.isna(previous_total) or previous_total == 0:
        total_delta = pd.NA
    else:
        total_delta = (total_value - previous_total) / previous_total * 100

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Dataset total", format_usd(total_value), format_pct(total_delta))
    k2.metric("Average YoY change", format_pct(avg_yoy))
    if top_row is not None:
        k3.metric("Largest economy", top_row["country"], format_usd(top_row["metric_value"]))
    else:
        k3.metric("Largest economy", "n/a")
    k4.metric("Economies covered", f"{year_df['country'].nunique()} of {wide['country'].nunique()}")

    st.plotly_chart(make_map(year_df, trade_flow, year))

    left, right = st.columns([0.9, 1.45])
    with left:
        st.subheader(f"{trade_flow} by economy")
        table = year_df[
            ["rank", "country", "region", "metric_value", "yoy_change_pct", "dataset_share_pct", "period"]
        ].copy()
        table = table.rename(
            columns={
                "rank": "#",
                "country": "Economy",
                "region": "Region",
                "metric_value": "US$",
                "yoy_change_pct": "YoY %",
                "dataset_share_pct": "Share %",
                "period": "Period",
            }
        )
        st.dataframe(
            table,
            width="stretch",
            hide_index=True,
            column_config={
                "US$": st.column_config.NumberColumn("US$", format="$%.0f"),
                "YoY %": st.column_config.NumberColumn("YoY %", format="%.1f"),
                "Share %": st.column_config.NumberColumn("Share %", format="%.2f"),
            },
            height=430,
        )
    with right:
        st.plotly_chart(make_regional_bar(year_df, trade_flow))

    trend_left, trend_right = st.columns(2)
    with trend_left:
        st.plotly_chart(make_country_trend(wide, selected_country))
    with trend_right:
        st.plotly_chart(make_aggregate_trend(wide))

    st.plotly_chart(make_index_chart(wide, trade_flow, metric_col, min(years)))

    st.markdown(
        f"""
        <div class="source-note">
            Source: <code>{DATA_PATH}</code>. Values are annual and expressed in current US dollars.
            The file provides annual observations through {max_year}; monthly and quarterly panels from the original WTO
            merchandise dashboard are intentionally omitted in this first tab.
        </div>
        """,
        unsafe_allow_html=True,
    )


def filter_tariff_data(df: pd.DataFrame) -> pd.DataFrame:
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    c1, c2, c3, c4 = st.columns([1.2, 1.1, 1.1, 1.0])
    with c1:
        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="tariff_date_range",
        )
    with c2:
        type_options = sorted(df["type"].dropna().unique())
        selected_types = st.multiselect("Action type", type_options, default=type_options, key="tariff_types")
    with c3:
        imposing_options = sorted(df["imposing_label"].dropna().unique())
        selected_imposers = st.multiselect(
            "Imposing economy",
            imposing_options,
            default=imposing_options,
            key="tariff_imposers",
        )
    with c4:
        weight_mode = st.selectbox(
            "Network weight",
            ["Estimated trade value", "Event count"],
            index=0,
            key="tariff_weight_mode",
        )

    f1, f2, f3 = st.columns([1.1, 1.35, 0.9])
    with f1:
        target_options = sorted(df["target_label"].dropna().unique())
        selected_targets = st.multiselect(
            "Target economy",
            target_options,
            default=target_options,
            key="tariff_targets",
        )
    with f2:
        sector_options = sorted(df["sector"].dropna().unique())
        selected_sectors = st.multiselect("Sector", sector_options, default=sector_options, key="tariff_sectors")
    with f3:
        retaliation_filter = st.selectbox(
            "Retaliation",
            ["All", "Retaliation only", "Initial/policy only"],
            index=0,
            key="tariff_retaliation",
        )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start_date, end_date = pd.to_datetime(min_date), pd.to_datetime(max_date)

    filtered = df[
        (df["date"] >= start_date)
        & (df["date"] <= end_date)
        & (df["type"].isin(selected_types))
        & (df["imposing_label"].isin(selected_imposers))
        & (df["target_label"].isin(selected_targets))
        & (df["sector"].isin(selected_sectors))
    ].copy()
    if retaliation_filter == "Retaliation only":
        filtered = filtered[filtered["retaliation"]]
    elif retaliation_filter == "Initial/policy only":
        filtered = filtered[~filtered["retaliation"]]
    return filtered, weight_mode


def render_tariff_tensions_tab() -> None:
    df = load_tariff_data(TARIFF_PATH)
    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Global Tariff Tensions</h1>
                <p>Tariff events, retaliations, affected sectors, and directed pressure between economies.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    filtered, weight_mode = filter_tariff_data(df)
    if filtered.empty:
        st.warning("No tariff events match the current filters.")
        return

    event_count = len(filtered)
    known_value = filtered["known_trade_value"].sum()
    known_count = int(filtered["trade_value_known"].sum())
    avg_rate = filtered["tariff_rate_pct"].mean()
    retaliation_share = filtered["retaliation"].mean() * 100
    edges = aggregate_tariff_edges(filtered, weight_mode)
    top_edge = edges.iloc[0] if not edges.empty else None

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tariff events", f"{event_count:,}")
    k2.metric("Known affected trade", f"${known_value:,.1f}B", f"{known_count} events with value")
    k3.metric("Average tariff rate", f"{avg_rate:.1f}%")
    k4.metric("Retaliation share", f"{retaliation_share:.1f}%")

    if top_edge is not None:
        suffix = "USD bn" if weight_mode == "Estimated trade value" else "events"
        st.caption(
            f"Strongest visible edge by {weight_mode.lower()}: "
            f"{top_edge['imposing_label']} -> {top_edge['target_label']} "
            f"({top_edge['weight']:,.1f} {suffix})."
        )

    trend_col, year_col = st.columns(2)
    with trend_col:
        st.plotly_chart(make_tariff_cumulative_chart(filtered))
    with year_col:
        st.plotly_chart(make_tariff_actions_by_year(filtered))

    map_left, map_right = st.columns(2)
    with map_left:
        st.plotly_chart(make_tariff_country_map(filtered, "imposing", weight_mode))
    with map_right:
        st.plotly_chart(make_tariff_country_map(filtered, "target", weight_mode))

    st.plotly_chart(make_tariff_network(filtered, weight_mode))

    sector_col, tree_col = st.columns([1, 1])
    with sector_col:
        st.plotly_chart(make_tariff_sector_bar(filtered, weight_mode))
    with tree_col:
        st.plotly_chart(make_tariff_type_treemap(filtered))

    dist_col, scatter_col = st.columns(2)
    with dist_col:
        st.plotly_chart(make_tariff_rate_distribution(filtered))
    with scatter_col:
        st.plotly_chart(make_tariff_rate_value_scatter(filtered))

    source_col, notes_col = st.columns([0.92, 1.08])
    with source_col:
        st.plotly_chart(make_tariff_source_chart(filtered))
    with notes_col:
        st.subheader("Filtered tariff events")
        table = filtered[
            [
                "date",
                "imposing_label",
                "target_label",
                "sector",
                "tariff_rate_pct",
                "tariff_rate_delta",
                "estimated_trade_value_usd_bn",
                "type",
                "retaliation_label",
                "legal_basis",
                "source",
                "notes",
            ]
        ].sort_values("date", ascending=False)
        table = table.rename(
            columns={
                "date": "Date",
                "imposing_label": "Imposing",
                "target_label": "Target",
                "sector": "Sector",
                "tariff_rate_pct": "Rate %",
                "tariff_rate_delta": "Delta %",
                "estimated_trade_value_usd_bn": "Trade value USD bn",
                "type": "Type",
                "retaliation_label": "Retaliation",
                "legal_basis": "Legal basis",
                "source": "Source",
                "notes": "Notes",
            }
        )
        st.dataframe(
            table,
            width="stretch",
            hide_index=True,
            height=430,
            column_config={
                "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Rate %": st.column_config.NumberColumn("Rate %", format="%.1f"),
                "Delta %": st.column_config.NumberColumn("Delta %", format="%.1f"),
                "Trade value USD bn": st.column_config.NumberColumn("Trade value USD bn", format="%.1f"),
            },
        )

    st.markdown(
        f"""
        <div class="source-note">
            Source: <code>{TARIFF_PATH}</code>. Missing affected-trade values are included in event-count views but excluded from
            value-weighted maps, Sankey flows, and network weights.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_financial_market_tab() -> None:
    df = load_stock_data(STOCK_PATH)
    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Financial Market Reaction</h1>
                <p>Stock-index performance, volatility, and tariff-event proximity across major markets.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    base = filter_by_date(df, "market")
    c1, c2 = st.columns([1, 1.25])
    with c1:
        countries = sorted(base["country"].dropna().unique())
        selected_countries = st.multiselect("Countries", countries, default=countries, key="market_countries")
    with c2:
        available_indices = sorted(base[base["country"].isin(selected_countries)]["index_name"].dropna().unique())
        selected_indices = st.multiselect("Market indices", available_indices, default=available_indices, key="market_indices")

    filtered = base[base["country"].isin(selected_countries) & base["index_name"].isin(selected_indices)].copy()
    if filtered.empty:
        st.warning("No market data match the current filters.")
        return

    latest = make_latest_table(filtered, ["country", "index_name"])
    leader = latest.sort_values("indexed_to_100", ascending=False).iloc[0]
    laggard = latest.sort_values("indexed_to_100", ascending=True).iloc[0]
    event_avg = filtered.loc[filtered["tariff_event_nearby"], "daily_return_pct"].mean()
    normal_avg = filtered.loc[~filtered["tariff_event_nearby"], "daily_return_pct"].mean()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Markets covered", f"{filtered['index_name'].nunique()}")
    k2.metric("Best latest index", leader["index_name"], f"{leader['indexed_to_100']:.1f}")
    k3.metric("Weakest latest index", laggard["index_name"], f"{laggard['indexed_to_100']:.1f}")
    k4.metric("Avg event-day return", format_pct(event_avg), f"Non-event {format_pct(normal_avg)}")

    st.plotly_chart(make_market_performance_chart(filtered))
    left, right = st.columns(2)
    with left:
        st.plotly_chart(make_market_event_box(filtered))
    with right:
        st.plotly_chart(make_market_annual_heatmap(filtered))
    left, right = st.columns(2)
    with left:
        st.plotly_chart(make_market_latest_bar(filtered))
    with right:
        st.plotly_chart(make_market_volatility_chart(filtered))

    st.markdown(
        f"""
        <div class="source-note">
            Source: <code>{STOCK_PATH}</code>. `indexed_to_100` compares market performance from a common baseline.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_exchange_rate_tab() -> None:
    df = load_currency_data(CURRENCY_PATH)
    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Exchange Rate Pressure</h1>
                <p>Currency movement against the US dollar, short-term volatility, and tariff-event effects.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    base = filter_by_date(df, "currency")
    c1, c2 = st.columns([1, 1])
    with c1:
        countries = sorted(base["country"].dropna().unique())
        selected_countries = st.multiselect("Countries", countries, default=countries, key="currency_countries")
    with c2:
        currencies = sorted(base[base["country"].isin(selected_countries)]["currency"].dropna().unique())
        selected_currencies = st.multiselect("Currencies", currencies, default=currencies, key="currency_codes")

    filtered = base[base["country"].isin(selected_countries) & base["currency"].isin(selected_currencies)].copy()
    if filtered.empty:
        st.warning("No currency data match the current filters.")
        return

    latest = make_latest_table(filtered, ["country", "currency"])
    pressure = latest.sort_values("pct_change_30d", ascending=False).iloc[0]
    relief = latest.sort_values("pct_change_30d", ascending=True).iloc[0]
    event_move = filtered.loc[filtered["tariff_event_nearby"], "pct_change_1d"].abs().mean()
    normal_move = filtered.loc[~filtered["tariff_event_nearby"], "pct_change_1d"].abs().mean()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Currencies covered", f"{filtered['currency'].nunique()}")
    k2.metric("Highest latest 30-day pressure", pressure["currency"], format_pct(pressure["pct_change_30d"]))
    k3.metric("Lowest latest 30-day pressure", relief["currency"], format_pct(relief["pct_change_30d"]))
    k4.metric("Avg abs event-day move", format_pct(event_move), f"Non-event {format_pct(normal_move)}")

    st.plotly_chart(make_currency_rate_chart(filtered))
    left, right = st.columns(2)
    with left:
        st.plotly_chart(make_currency_volatility_chart(filtered))
    with right:
        st.plotly_chart(make_currency_event_box(filtered))
    left, right = st.columns(2)
    with left:
        st.plotly_chart(make_currency_latest_pressure(filtered))
    with right:
        st.plotly_chart(make_currency_change_heatmap(filtered))

    st.markdown(
        f"""
        <div class="source-note">
            Source: <code>{CURRENCY_PATH}</code>. Higher `rate_vs_usd` means more local-currency units per US dollar.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sector_impact_tab() -> None:
    df = load_sector_data(SECTOR_PATH)
    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Sectoral Impact</h1>
                <p>Sector ETF performance and volatility by country and tariff sensitivity.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    base = filter_by_date(df, "sector")
    c1, c2, c3 = st.columns([0.85, 1.25, 0.9])
    with c1:
        countries = sorted(base["country"].dropna().unique())
        selected_countries = st.multiselect("Countries", countries, default=countries, key="sector_countries")
    with c2:
        sectors = sorted(base[base["country"].isin(selected_countries)]["sector"].dropna().unique())
        selected_sectors = st.multiselect("Sectors", sectors, default=sectors, key="sector_names")
    with c3:
        sensitivities = sorted(base["tariff_sensitivity"].dropna().unique())
        selected_sensitivities = st.multiselect(
            "Tariff sensitivity",
            sensitivities,
            default=sensitivities,
            key="sector_sensitivities",
        )

    filtered = base[
        base["country"].isin(selected_countries)
        & base["sector"].isin(selected_sectors)
        & base["tariff_sensitivity"].isin(selected_sensitivities)
    ].copy()
    if filtered.empty:
        st.warning("No sector data match the current filters.")
        return

    latest = make_latest_table(filtered, ["country", "sector"])
    best = latest.sort_values("indexed_to_100", ascending=False).iloc[0]
    worst = latest.sort_values("indexed_to_100", ascending=True).iloc[0]
    high_share = (latest["tariff_sensitivity"] == "High").mean() * 100

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Sector-country pairs", f"{len(latest):,}")
    k2.metric("Best latest sector", best["sector_label"], f"{best['indexed_to_100']:.1f}")
    k3.metric("Weakest latest sector", worst["sector_label"], f"{worst['indexed_to_100']:.1f}")
    k4.metric("High-sensitivity share", f"{high_share:.1f}%")

    st.plotly_chart(make_sector_performance_chart(filtered))
    left, right = st.columns(2)
    with left:
        st.plotly_chart(make_sector_latest_heatmap(filtered))
    with right:
        st.plotly_chart(make_sector_return_distribution(filtered))
    st.plotly_chart(make_sector_volatility_bar(filtered))

    st.markdown(
        f"""
        <div class="source-note">
            Source: <code>{SECTOR_PATH}</code>. Sector data covers USA, China, and global ETFs.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_vietnam_impact_tab() -> None:
    macro = load_macro_data(DATA_PATH)
    stock = load_stock_data(STOCK_PATH)
    currency = load_currency_data(CURRENCY_PATH)
    tariffs = load_tariff_data(TARIFF_PATH)
    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Vietnam Impact</h1>
                <p>Vietnam-specific trade, macro, currency, and market signals under global tariff tensions.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    vn_macro = macro[macro["country"] == "Vietnam"].copy()
    vn_stock = stock[stock["country"] == "Vietnam"].copy()
    vn_currency = currency[currency["country"] == "Vietnam"].copy()
    vn_tariffs = tariffs[(tariffs["imposing_norm"] == "VNM") | (tariffs["target_norm"] == "VNM")].copy()

    latest_year = int(vn_macro["year"].max())
    latest_macro = vn_macro[vn_macro["year"] == latest_year]
    trade_gdp = latest_macro.loc[latest_macro["indicator_name"] == "Trade (% of GDP)", "value"]
    gdp_growth = latest_macro.loc[latest_macro["indicator_name"] == "GDP growth (annual %)", "value"]
    latest_stock = vn_stock.sort_values("date").tail(1)
    latest_vnd = vn_currency.sort_values("date").tail(1)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Latest macro year", str(latest_year))
    k2.metric("Trade openness", f"{trade_gdp.iloc[0]:.1f}%" if not trade_gdp.empty else "n/a")
    k3.metric("GDP growth", format_pct(gdp_growth.iloc[0]) if not gdp_growth.empty else "n/a")
    if not latest_stock.empty:
        k4.metric("VN-Index latest", f"{latest_stock.iloc[0]['indexed_to_100']:.1f}")
    else:
        k4.metric("VN-Index latest", "n/a")

    left, right = st.columns([1.25, 1])
    with left:
        st.plotly_chart(make_vietnam_trade_chart(macro))
    with right:
        st.plotly_chart(make_vietnam_market_currency_chart(stock, currency))
        if not latest_vnd.empty:
            st.metric("Latest VND per USD", f"{latest_vnd.iloc[0]['rate_vs_usd']:,.0f}", format_pct(latest_vnd.iloc[0]["pct_change_30d"]))
        if vn_tariffs.empty:
            st.info("No direct Vietnam-imposing or Vietnam-targeted tariff events are recorded in tariff_timeline.csv.")
        else:
            st.dataframe(vn_tariffs.sort_values("date", ascending=False), width="stretch", hide_index=True, height=220)

    vn_table = vn_macro.pivot_table(index=["year", "period"], columns="indicator_name", values="value", aggfunc="mean").reset_index()
    st.subheader("Vietnam annual indicator table")
    st.dataframe(vn_table.sort_values("year", ascending=False), width="stretch", hide_index=True, height=360)

    st.markdown(
        f"""
        <div class="source-note">
            Sources: <code>{DATA_PATH}</code>, <code>{STOCK_PATH}</code>, <code>{CURRENCY_PATH}</code>, and <code>{TARIFF_PATH}</code>.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_macro_adjustment_tab() -> None:
    macro = load_macro_data(DATA_PATH)
    inflation = load_inflation_data(INFLATION_PATH)
    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Long-term Macro Adjustment</h1>
                <p>Annual trade/macro shifts and US monthly adjustment indicators across trade-war eras.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 1.4])
    with c1:
        country_options = sorted(macro["country"].dropna().unique())
        default_countries = [c for c in ["USA", "China", "Vietnam", "Germany", "India"] if c in country_options]
        selected_countries = st.multiselect(
            "Countries",
            country_options,
            default=default_countries or country_options[:5],
            key="macro_countries",
        )
    with c2:
        indicator_options = sorted(macro["indicator_name"].dropna().unique())
        default_indicators = [
            "GDP growth (annual %)",
            "Trade (% of GDP)",
            "Exports of goods & services (USD)",
            "Imports of goods & services (USD)",
        ]
        selected_indicators = st.multiselect(
            "Macro indicators",
            indicator_options,
            default=[i for i in default_indicators if i in indicator_options],
            key="macro_indicators",
        )

    if not selected_countries or not selected_indicators:
        st.warning("Select at least one country and one indicator.")
        return

    latest_year = int(macro["year"].max())
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Countries", f"{len(selected_countries)}")
    k2.metric("Indicators", f"{len(selected_indicators)}")
    k3.metric("Annual range", f"{int(macro['year'].min())}-{latest_year}")
    k4.metric("US monthly range", f"{inflation['date'].min().year}-{inflation['date'].max().year}")

    st.plotly_chart(make_macro_indicator_chart(macro, selected_countries, selected_indicators))

    left, right = st.columns(2)
    with left:
        box_indicator = st.selectbox("Period distribution indicator", selected_indicators, key="macro_box_indicator")
        st.plotly_chart(make_macro_period_box(macro[macro["country"].isin(selected_countries)], box_indicator))
    with right:
        st.plotly_chart(make_macro_latest_heatmap(macro[macro["country"].isin(selected_countries)], selected_indicators))

    left, right = st.columns(2)
    with left:
        st.plotly_chart(make_macro_correlation_heatmap(macro[macro["country"].isin(selected_countries)], selected_indicators))
    with right:
        metrics = sorted(inflation["metric"].dropna().unique())
        default_metrics = [m for m in ["CPI", "PPI", "Trade Balance", "Unemployment", "Interest Rate"] if m in metrics]
        selected_metrics = st.multiselect("US adjustment metrics", metrics, default=default_metrics, key="usa_adjustment_metrics")
        if selected_metrics:
            st.plotly_chart(make_usa_adjustment_chart(inflation, selected_metrics))
        else:
            st.info("Select at least one US adjustment metric.")

    st.markdown(
        f"""
        <div class="source-note">
            Sources: <code>{DATA_PATH}</code> for annual macro/trade indicators and <code>{INFLATION_PATH}</code> for US monthly adjustment series.
        </div>
        """,
        unsafe_allow_html=True,
    )


tabs = st.tabs(
    [
        "Trade Volume",
        "Global Tariff Tensions",
        "Financial Market Reaction",
        "Exchange Rate Pressure",
        "Sectoral Impact",
        "Vietnam Impact",
        "Long-term Macro Adjustment",
    ]
)
with tabs[0]:
    render_trade_volume_tab()
with tabs[1]:
    render_tariff_tensions_tab()
with tabs[2]:
    render_financial_market_tab()
with tabs[3]:
    render_exchange_rate_tab()
with tabs[4]:
    render_sector_impact_tab()
with tabs[5]:
    render_vietnam_impact_tab()
with tabs[6]:
    render_macro_adjustment_tab()
