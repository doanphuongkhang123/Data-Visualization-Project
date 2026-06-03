from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DATA_PATH = APP_DIR.parent / "new" / "trade_volume_annual.csv"

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
    total_delta = ((total_value - previous_total) / previous_total * 100) if previous_total and not pd.isna(previous_total) else pd.NA

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


tabs = st.tabs(["Trade Volume"])
with tabs[0]:
    render_trade_volume_tab()
