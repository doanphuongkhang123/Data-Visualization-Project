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
TRADE_GDP = "Trade (% of GDP)"
GDP_GROWTH = "GDP growth (annual %)"
FDI_INFLOW = "FDI net inflows (USD)"
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


def configure_page() -> None:
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
    df["iso3"] = df["country"].map(lambda c: COUNTRY_META.get(c, {}).get("iso3", c))
    df["region"] = df["country"].map(lambda c: COUNTRY_META.get(c, {}).get("region", "Other"))
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


def format_pct_plain(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:.1f}%"


def short_indicator_name(indicator_name: str) -> str:
    return {
        EXPORTS: "Exports",
        IMPORTS: "Imports",
        FDI_INFLOW: "FDI inflows",
        GDP_GROWTH: "GDP growth",
        TRADE_GDP: "Trade/GDP",
    }.get(indicator_name, indicator_name)


def latest_indicator_snapshot(
    df: pd.DataFrame,
    indicator: str | list[str],
    aggfunc: str = "sum",
) -> tuple[float, int | None]:
    indicators = [indicator] if isinstance(indicator, str) else indicator
    work = df[df["indicator_name"].isin(indicators)].dropna(subset=["value"]).copy()
    if work.empty:
        return math.nan, None
    latest_year = int(work["year"].max())
    latest = work[work["year"] == latest_year]
    if aggfunc == "mean":
        return latest["value"].mean(), latest_year
    return latest["value"].sum(), latest_year


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


def filter_annual_macro(
    df: pd.DataFrame,
    countries: list[str],
    periods: list[str],
    year_range: tuple[int, int],
) -> pd.DataFrame:
    start_year, end_year = year_range
    return df[
        (df["country"].isin(countries))
        & (df["period"].isin(periods))
        & (df["year"] >= start_year)
        & (df["year"] <= end_year)
    ].copy()


def make_trade_import_export_chart(df: pd.DataFrame, trade_flow: str) -> go.Figure:
    indicator = EXPORTS if trade_flow == "Exports" else IMPORTS if trade_flow == "Imports" else None
    title = (
        f"{trade_flow} by country"
        if trade_flow in ["Exports", "Imports"]
        else "Selected trade flow by country"
    )
    if indicator is None:
        return go.Figure().update_layout(title=title, height=500)
    work = df[df["indicator_name"] == indicator].dropna(subset=["value"]).copy()
    work["formatted_value"] = work["value"].map(format_usd)
    fig = px.line(
        work,
        x="year",
        y="value",
        color="country",
        markers=True,
        custom_data=["country", "period", "indicator_name", "formatted_value"],
        title=f"{title}<br><sup>Values shown in current USD.</sup>",
        labels={"year": "", "value": "US dollars", "country": "Country"},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>Year: %{x}<br>Period: %{customdata[1]}"
            "<br>Indicator: %{customdata[2]}<br>Displayed value: %{customdata[3]}"
            "<br>Original value: $%{y:,.0f}<extra></extra>"
        )
    )
    fig.update_layout(
        height=500,
        yaxis=dict(tickformat="~s", gridcolor="#e9edf3"),
        xaxis=dict(dtick=1),
        legend=dict(orientation="h", y=-0.25, x=0),
    )
    return fig


def make_yoy_change_by_period_chart(df: pd.DataFrame, indicators: list[str], robust_display: bool = True) -> go.Figure:
    work = df[df["indicator_name"].isin(indicators)].dropna(subset=["yoy_change_pct"]).copy()
    if work.empty:
        return go.Figure().update_layout(title="YoY change distribution by trade-war period", height=470)
    y_col = "yoy_change_pct"
    y_label = "YoY change (%)"
    subtitle = ""
    if robust_display:
        bounds = work.groupby("indicator_name")["yoy_change_pct"].quantile([0.05, 0.95]).unstack()
        lower = work["indicator_name"].map(bounds[0.05])
        upper = work["indicator_name"].map(bounds[0.95])
        work["display_yoy_change_pct"] = work["yoy_change_pct"].clip(lower=lower, upper=upper)
        y_col = "display_yoy_change_pct"
        y_label = "YoY change, clipped to 5th-95th percentile (%)"
        subtitle = " (robust display)"
    work["displayed_yoy"] = work[y_col].map(format_pct_plain)
    work["original_yoy"] = work["yoy_change_pct"].map(format_pct_plain)
    fig = px.box(
        work,
        x="period",
        y=y_col,
        color="indicator_name",
        points="all",
        category_orders={"period": PERIOD_ORDER},
        custom_data=["country", "year", "period", "indicator_name", "displayed_yoy", "original_yoy"],
        title=f"YoY change distribution by trade-war period{subtitle}",
        labels={"period": "", y_col: y_label, "indicator_name": "Indicator"},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>Year: %{customdata[1]}<br>Period: %{customdata[2]}"
            "<br>Indicator: %{customdata[3]}<br>Displayed value: %{customdata[4]}"
            "<br>Original value: %{customdata[5]}<extra></extra>"
        )
    )
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="#667085")
    fig.update_layout(
        height=470,
        yaxis=dict(gridcolor="#e9edf3"),
        legend=dict(orientation="h", y=-0.25, x=0),
    )
    return fig


def make_trade_gdp_chart(df: pd.DataFrame) -> go.Figure:
    work = df[df["indicator_name"] == TRADE_GDP].dropna(subset=["value"]).copy()
    work["formatted_value"] = work["value"].map(format_pct_plain)
    fig = px.line(
        work,
        x="year",
        y="value",
        color="country",
        markers=True,
        custom_data=["country", "period", "indicator_name", "formatted_value"],
        title="Trade as a share of GDP",
        labels={"year": "", "value": "Trade (% of GDP)", "country": "Country"},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>Year: %{x}<br>Period: %{customdata[1]}"
            "<br>Indicator: %{customdata[2]}<br>Displayed value: %{customdata[3]}"
            "<br>Original value: %{y:.2f}%<extra></extra>"
        )
    )
    fig.update_layout(
        height=440,
        yaxis=dict(ticksuffix="%", gridcolor="#e9edf3"),
        xaxis=dict(dtick=1),
        legend=dict(orientation="h", y=-0.25, x=0),
    )
    return fig


def make_gdp_growth_period_chart(df: pd.DataFrame) -> go.Figure:
    work = df[df["indicator_name"] == GDP_GROWTH].dropna(subset=["value"]).copy()
    avg = (
        work.groupby(["period", "country"], as_index=False)["value"]
        .mean()
        .rename(columns={"value": "avg_gdp_growth"})
    )
    if avg.empty:
        return go.Figure().update_layout(title="Average GDP growth by period", height=440)
    avg["displayed_value"] = avg["avg_gdp_growth"].map(format_pct_plain)
    if avg["country"].nunique() > 6:
        matrix = avg.pivot_table(index="country", columns="period", values="avg_gdp_growth", aggfunc="mean")
        matrix = matrix.reindex(columns=[p for p in PERIOD_ORDER if p in matrix.columns])
        fig = px.imshow(
            matrix,
            aspect="auto",
            color_continuous_scale="RdBu",
            color_continuous_midpoint=0,
            title="Average GDP growth by period",
            labels=dict(x="", y="", color="GDP growth (%)"),
        )
        fig.update_traces(
            hovertemplate="<b>%{y}</b><br>Period: %{x}<br>Displayed value: %{z:.1f}%<br>Original value: %{z:.2f}%<extra></extra>"
        )
        fig.update_layout(height=440, margin=dict(l=0, r=0, t=56, b=0))
        return fig
    fig = px.bar(
        avg,
        x="period",
        y="avg_gdp_growth",
        color="country",
        barmode="group",
        category_orders={"period": PERIOD_ORDER},
        custom_data=["country", "period", "displayed_value"],
        title="Average GDP growth by period",
        labels={"period": "", "avg_gdp_growth": "GDP growth (%)", "country": "Country"},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>Period: %{customdata[1]}<br>Indicator: GDP growth"
            "<br>Displayed value: %{customdata[2]}<br>Original value: %{y:.2f}%<extra></extra>"
        )
    )
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="#667085")
    yaxis = dict(ticksuffix="%", gridcolor="#e9edf3")
    if avg["avg_gdp_growth"].min() >= 0:
        yaxis["rangemode"] = "tozero"
    fig.update_layout(
        height=440,
        yaxis=yaxis,
        legend=dict(orientation="h", y=-0.27, x=0),
    )
    return fig


def make_fdi_inflows_chart(df: pd.DataFrame, display_mode: str = "Absolute USD") -> go.Figure:
    work = df[df["indicator_name"] == FDI_INFLOW].dropna(subset=["value"]).copy()
    if work.empty:
        return go.Figure().update_layout(title="FDI net inflows by year", height=440)
    y_col = "value"
    y_label = "US dollars"
    title_suffix = "current USD"
    if display_mode == "Indexed to 100":
        indexed_frames = []
        for _, country_df in work.sort_values(["country", "year"]).groupby("country"):
            base = country_df.loc[country_df["value"].notna() & (country_df["value"] != 0), "value"]
            if base.empty:
                continue
            country_df = country_df.copy()
            country_df["indexed_value"] = country_df["value"] / base.iloc[0] * 100
            indexed_frames.append(country_df)
        work = pd.concat(indexed_frames, ignore_index=True) if indexed_frames else work.iloc[0:0].copy()
        y_col = "indexed_value"
        y_label = "Index, first available year = 100"
        title_suffix = "indexed to 100"
        if work.empty:
            return go.Figure().update_layout(title=f"FDI net inflows by year ({title_suffix})", height=440)
    work["formatted_value"] = work["value"].map(format_usd)
    if display_mode == "Indexed to 100":
        work["displayed_value"] = work[y_col].map(lambda v: "n/a" if pd.isna(v) else f"{v:.1f}")
    else:
        work["displayed_value"] = work["formatted_value"]
    fig = px.line(
        work,
        x="year",
        y=y_col,
        color="country",
        markers=True,
        custom_data=["country", "period", "indicator_name", "displayed_value", "formatted_value"],
        title=f"FDI net inflows by year ({title_suffix})",
        labels={"year": "", y_col: y_label, "country": "Country"},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>Year: %{x}<br>Period: %{customdata[1]}"
            "<br>Indicator: %{customdata[2]}<br>Displayed value: %{customdata[3]}"
            "<br>Original value: %{customdata[4]}<extra></extra>"
        )
    )
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="#667085")
    yaxis = dict(gridcolor="#e9edf3")
    if display_mode == "Absolute USD":
        yaxis["tickformat"] = "~s"
    fig.update_layout(
        height=440,
        yaxis=yaxis,
        xaxis=dict(dtick=1),
        legend=dict(orientation="h", y=-0.25, x=0),
    )
    return fig


def make_macro_performance_heatmap(df: pd.DataFrame) -> go.Figure:
    indicator = GDP_GROWTH if GDP_GROWTH in df["indicator_name"].unique() else None
    color_title = "Avg GDP growth (%)"
    if indicator is None:
        yoy = df.dropna(subset=["yoy_change_pct"]).copy()
        if yoy.empty:
            return go.Figure().update_layout(title="Macro performance by country and trade-war period", height=430)
        heat = (
            yoy.groupby(["country", "period"], as_index=False)["yoy_change_pct"]
            .mean()
            .rename(columns={"yoy_change_pct": "metric"})
        )
        color_title = "Avg YoY change (%)"
    else:
        heat = (
            df[df["indicator_name"] == indicator]
            .dropna(subset=["value"])
            .groupby(["country", "period"], as_index=False)["value"]
            .mean()
            .rename(columns={"value": "metric"})
        )
    matrix = heat.pivot_table(index="country", columns="period", values="metric", aggfunc="mean")
    matrix = matrix.reindex(columns=[p for p in PERIOD_ORDER if p in matrix.columns])
    fig = px.imshow(
        matrix,
        aspect="auto",
        color_continuous_scale="RdBu",
        color_continuous_midpoint=0,
        title="Macro performance by country and trade-war period",
        labels=dict(x="", y="", color=color_title),
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Period: %{x}<br>Displayed value: %{z:.1f}%<br>Original value: %{z:.2f}%<extra></extra>"
    )
    fig.update_layout(height=430, margin=dict(l=0, r=0, t=56, b=0))
    return fig


def make_macro_period_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    indicators = [EXPORTS, IMPORTS, TRADE_GDP, GDP_GROWTH, FDI_INFLOW]
    summary = (
        df[df["indicator_name"].isin(indicators)]
        .groupby(["period", "indicator_name"], as_index=False)
        .agg(
            average_value=("value", "mean"),
            median_yoy_change_pct=("yoy_change_pct", "median"),
            observations=("value", "count"),
        )
    )
    summary["period"] = pd.Categorical(summary["period"], categories=PERIOD_ORDER, ordered=True)
    summary["indicator_label"] = summary["indicator_name"].map(short_indicator_name)
    return summary.sort_values(["period", "indicator_name"])


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


