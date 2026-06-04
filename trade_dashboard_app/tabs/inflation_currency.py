from html import escape

from core import *


DEFAULT_METRICS = ["CPI", "PPI", "PCE", "Import Price Index"]
DEFAULT_COUNTRIES = ["Australia", "Canada", "Singapore"]
PLOTLY_CONFIG = {"displayModeBar": "hover", "displaylogo": False, "scrollZoom": False}
PAGE5_BLUE = "#0072B2"
PAGE5_ORANGE = "#D55E00"
PAGE5_GREEN = "#009E73"
CURRENCY_COLOR_MAP = {
    "AUD": "#2a9d8f",
    "CAD": "#8e5ea2",
    "SGD": "#f4a261",
    "CNY": "#6a994e",
    "EUR": "#a17c6b",
    "GBP": "#7f7f7f",
    "INR": "#bc6c25",
    "JPY": "#b08968",
    "KRW": "#6d597a",
    "MXN": "#588157",
    "MYR": "#a98467",
    "THB": "#7b2cbf",
    "TWD": "#52796f",
    "VND": "#2d6a4f",
}
COUNTRY_COLOR_MAP = {
    "Australia": "#2a9d8f",
    "Canada": "#8e5ea2",
    "Singapore": "#f4a261",
    "China": "#6a994e",
    "European Union": "#a17c6b",
    "Japan": "#b08968",
    "South Korea": "#6d597a",
    "Vietnam": "#2d6a4f",
}
CURRENCY_TARIFF_ALIASES = {
    "AUD": {"AUS", "Australia"},
    "BRL": {"BRA", "Brazil"},
    "CAD": {"CAN", "Canada"},
    "CNY": {"CHN", "China"},
    "EUR": {"EU", "EU27", "European Union"},
    "GBP": {"GBR", "UK", "United Kingdom"},
    "INR": {"IND", "India"},
    "JPY": {"JPN", "Japan"},
    "KRW": {"KOR", "South Korea"},
    "MXN": {"MEX", "Mexico"},
    "MYR": {"MYS", "Malaysia"},
    "SGD": {"SGP", "Singapore"},
    "THB": {"THA", "Thailand"},
    "TWD": {"TWN", "Taiwan"},
    "VND": {"VNM", "Vietnam"},
}
BROAD_TARGETS = {"ALL", "Global", "GLOBAL"}
ERA_CONTEXT_COLORS = {
    "Pre-Trade War": PERIOD_COLORS.get("Pre-Trade War", "#5B8C7A"),
    "Trade War 1.0": PERIOD_COLORS.get("Trade War 1.0", "#D9895B"),
    "Recovery": PERIOD_COLORS.get("Recovery", "#4C78A8"),
    "Trade War 2.0": PERIOD_COLORS.get("Trade War 2.0", "#B15C63"),
}
ERA_DATE_SPANS = [
    ("Pre-Trade War", pd.Timestamp("2015-01-01"), pd.Timestamp("2018-02-28")),
    ("Trade War 1.0", pd.Timestamp("2018-03-01"), pd.Timestamp("2019-12-31")),
    ("Recovery", pd.Timestamp("2020-01-01"), pd.Timestamp("2023-12-31")),
    ("Trade War 2.0", pd.Timestamp("2024-01-01"), None),
]
ERA_CONTEXT_LABELS = {
    "Pre-Trade War": "Pre-Trade War",
    "Trade War 1.0": "Trade War 1.0",
    "Recovery": "Recovery",
    "Trade War 2.0": "Trade War 2.0",
}
ERA_TO_PERIOD_LABEL = {"Phase 1 + COVID": "Recovery"}


def _option_key(option: str) -> str:
    return (
        str(option)
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        .replace("&", "and")
        .replace(".", "")
    )


def _set_all_checkboxes(options: list[str], key_prefix: str) -> None:
    select_all = st.session_state.get(f"{key_prefix}_select_all", False)
    for option in options:
        st.session_state[f"{key_prefix}_{_option_key(option)}"] = select_all


def _sync_select_all(options: list[str], key_prefix: str) -> None:
    st.session_state[f"{key_prefix}_select_all"] = all(
        st.session_state.get(f"{key_prefix}_{_option_key(option)}", False) for option in options
    )


def _checkbox_dropdown(label: str, options: list[str], default: list[str], key_prefix: str) -> list[str]:
    for option in options:
        st.session_state.setdefault(f"{key_prefix}_{_option_key(option)}", option in default)
    st.session_state.setdefault(
        f"{key_prefix}_select_all",
        all(st.session_state.get(f"{key_prefix}_{_option_key(option)}", False) for option in options),
    )

    selected = []
    selected_count = sum(
        1 for option in options if st.session_state.get(f"{key_prefix}_{_option_key(option)}", option in default)
    )
    with st.popover(f"{label} ({selected_count})", use_container_width=True):
        st.checkbox(
            "Select all",
            key=f"{key_prefix}_select_all",
            on_change=_set_all_checkboxes,
            args=(options, key_prefix),
        )
        for option in options:
            checked = st.checkbox(
                option,
                key=f"{key_prefix}_{_option_key(option)}",
                on_change=_sync_select_all,
                args=(options, key_prefix),
            )
            if checked:
                selected.append(option)
    return selected


def format_usd_millions_as_billions(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value) / 1_000:,.1f}B"


def add_era_context_to_date_chart(
    fig: go.Figure,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    label_y: float = 1.07,
    short_label_y: float = 1.08,
) -> go.Figure:
    if pd.isna(start_date) or pd.isna(end_date):
        return fig

    for era, era_start, era_end in ERA_DATE_SPANS:
        span_start = max(era_start, start_date)
        span_end = min(era_end or end_date, end_date)
        if span_start > span_end:
            continue

        color = ERA_CONTEXT_COLORS.get(era, "#8d99ae")
        midpoint = span_start + (span_end - span_start) / 2
        span_days = (span_end - span_start).days
        fig.add_vrect(
            x0=span_start,
            x1=span_end,
            fillcolor=color,
            opacity=0.08,
            layer="below",
            line_width=0,
        )
        label_x = midpoint
        annotation_y = label_y
        xanchor = "center"
        if span_days < 365:
            label_x = span_end - pd.Timedelta(days=18)
            annotation_y = short_label_y
            xanchor = "right"
        fig.add_annotation(
            x=label_x,
            y=annotation_y,
            xref="x",
            yref="paper",
            text=ERA_CONTEXT_LABELS.get(era, era),
            showarrow=False,
            xanchor=xanchor,
            font=dict(size=10, color=color),
            bgcolor="rgba(255,255,255,0.72)",
            bordercolor=color,
            borderwidth=1,
            borderpad=3,
        )

    for boundary in [pd.Timestamp("2018-03-01"), pd.Timestamp("2020-01-01"), pd.Timestamp("2024-01-01")]:
        if start_date < boundary < end_date:
            fig.add_vline(
                x=boundary,
                line_width=1,
                line_dash="dot",
                line_color="#98a2b3",
                opacity=0.75,
            )
    return fig


def render_kpi_row(items: list[tuple[str, str, str]]) -> None:
    cards = "".join(
        (
            f'<div class="page5-kpi" style="border-top-color: {escape(str(accent))}; color: {escape(str(accent))};">'
            f'<strong style="color: {escape(str(accent))};">{escape(str(value))}</strong>'
            f"<span>{escape(str(label))}</span>"
            "</div>"
        )
        for label, value, accent in items
    )
    st.markdown(f'<div class="page5-kpis">{cards}</div>', unsafe_allow_html=True)


def filter_inflation_currency_data(inflation: pd.DataFrame, currency: pd.DataFrame):
    metric_options = sorted(inflation["metric"].dropna().unique())
    country_options = sorted(currency["country"].dropna().unique())
    default_countries = [country for country in DEFAULT_COUNTRIES if country in country_options]

    c_year, c1, c2, c3 = st.columns(
        4,
        vertical_alignment="bottom",
    )
    with c1:
        selected_metrics = _checkbox_dropdown(
            "Metric",
            metric_options,
            [m for m in DEFAULT_METRICS if m in metric_options],
            "page5_metrics",
        )
    with c2:
        selected_countries = _checkbox_dropdown(
            "Country / economy",
            country_options,
            default_countries or country_options[:6],
            "page5_countries_v2",
        )

    currency_base = currency[currency["country"].isin(selected_countries)].copy()
    currency_options = sorted(currency_base["currency"].dropna().unique())
    with c3:
        selected_currencies = _checkbox_dropdown(
            "Currency",
            currency_options,
            currency_options,
            "page5_currencies",
        )

    inflation_base = inflation.copy()
    inflation_base["period"] = inflation_base["era"].replace(ERA_TO_PERIOD_LABEL)
    currency_base = currency_base[currency_base["currency"].isin(selected_currencies)].copy()

    date_bounds = []
    if not inflation_base.empty:
        date_bounds.append((inflation_base["date"].min(), inflation_base["date"].max()))
    if not currency_base.empty:
        date_bounds.append((currency_base["date"].min(), currency_base["date"].max()))

    if not date_bounds:
        st.warning("No rows are available for the selected metric, country, and currency filters.")
        return inflation.iloc[0:0].copy(), inflation.iloc[0:0].copy(), currency.iloc[0:0].copy(), selected_metrics

    min_date = min(start for start, _ in date_bounds).date()
    max_date = max(end for _, end in date_bounds).date()
    min_year = min_date.year
    max_year = max_date.year
    with c_year:
        selected_year_range = st.slider(
            "Year range",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year),
            step=1,
            key=f"page5_year_range_{min_year}_{max_year}",
        )

    if isinstance(selected_year_range, tuple) and len(selected_year_range) == 2:
        start_year, end_year = selected_year_range
    else:
        start_year, end_year = min_year, max_year

    start_date = max(pd.Timestamp(year=int(start_year), month=1, day=1), pd.to_datetime(min_date))
    end_date = min(pd.Timestamp(year=int(end_year), month=12, day=31), pd.to_datetime(max_date))

    if start_date > end_date:
        st.warning("Start date must be before end date.")
        return inflation.iloc[0:0].copy(), inflation.iloc[0:0].copy(), currency.iloc[0:0].copy(), selected_metrics

    inflation_filtered = inflation_base[
        (inflation_base["date"] >= start_date)
        & (inflation_base["date"] <= end_date)
    ].copy()

    currency_filtered = currency_base[
        (currency_base["date"] >= start_date)
        & (currency_base["date"] <= end_date)
    ].copy()

    metric_filtered = inflation_filtered[inflation_filtered["metric"].isin(selected_metrics)].copy()
    return inflation_filtered, metric_filtered, currency_filtered, selected_metrics


def make_price_response_chart(df: pd.DataFrame, compact: bool = False) -> go.Figure:
    core = df[
        ((df["metric"] == "CPI") & (df["category"] == "All Items"))
        | (df["metric"].isin(["PPI", "PCE"]))
    ].copy()
    core["display_metric"] = core["metric"].map(
        {
            "CPI": "Consumer Price Index",
            "PPI": "Producer Price Index",
            "PCE": "Personal Consumption Expenditures",
        }
    )
    fig = px.line(
        core,
        x="date",
        y="value",
        color="display_metric",
        title="United States price indexes" if compact else "United States consumer, producer, and consumption price indexes",
        labels={"date": "Date", "value": "Index value", "display_metric": "Price index"},
    )
    fig.update_yaxes(gridcolor="#e9edf3")
    if compact:
        fig.update_layout(
            height=320,
            showlegend=True,
            title_font_size=13,
            legend=dict(
                orientation="h",
                y=-0.22,
                x=0,
                font=dict(size=10),
                title=dict(text="Price index", font=dict(size=10)),
            ),
            margin=dict(l=44, r=8, t=44, b=78),
        )
        fig.update_xaxes(title="Date", tickfont=dict(size=10))
        fig.update_yaxes(title="Index value", title_font=dict(size=11), tickfont=dict(size=10))
        return fig
    fig.update_layout(
        height=430,
        showlegend=True,
        title_font_size=14,
        legend=dict(orientation="h", y=-0.18, x=0),
        margin=dict(l=50, r=28, t=58, b=72),
    )
    return fig


def make_average_yoy_by_era_chart(df: pd.DataFrame, compact: bool = False) -> go.Figure:
    work = df.dropna(subset=["yoy_change_pct"]).copy()
    work["period"] = work["era"].replace(ERA_TO_PERIOD_LABEL)
    period_display = {
        "Pre-Trade War": "Pre-Trade<br>War",
        "Trade War 1.0": "Trade War<br>1.0",
        "Recovery": "Recovery",
        "Trade War 2.0": "Trade War<br>2.0",
    }
    work["period_display"] = work["period"].map(period_display).fillna(work["period"])
    avg = work.groupby(["period", "metric"], as_index=False)["yoy_change_pct"].mean()
    avg["period_display"] = avg["period"].map(period_display).fillna(avg["period"])
    fig = px.bar(
        avg,
        x="period_display",
        y="yoy_change_pct",
        color="metric",
        barmode="group",
        category_orders={
            "period_display": ["Pre-Trade<br>War", "Trade War<br>1.0", "Recovery", "Trade War<br>2.0"],
            "metric": ["CPI", "Import Price Index", "PCE", "PPI"],
        },
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Average year-over-year change" if compact else "Average year-over-year change by period",
        labels={"period_display": "Trade-war period", "yoy_change_pct": "Year-over-year change (%)", "metric": "Metric"},
    )
    if compact:
        for trace in fig.data:
            if trace.name == "Import Price Index":
                trace.name = "Import Price<br>Index"
        fig.update_layout(
            height=320,
            title_font_size=13,
            yaxis=dict(gridcolor="#e9edf3"),
            legend=dict(
                orientation="h",
                y=-0.20,
                x=0,
                font=dict(size=9),
                title=dict(text=""),
                entrywidth=92,
                entrywidthmode="pixels",
            ),
            margin=dict(l=52, r=8, t=44, b=70),
        )
        fig.update_xaxes(title="", tickfont=dict(size=10))
        fig.update_yaxes(title="Year-over-year change (%)", title_font=dict(size=11), tickfont=dict(size=10))
        return fig
    fig.update_layout(
        height=310,
        title_font_size=14,
        yaxis=dict(gridcolor="#e9edf3"),
        legend=dict(orientation="h", y=-0.28, x=0, title=dict(text=""), entrywidth=118, entrywidthmode="pixels"),
        margin=dict(l=54, r=14, t=50, b=74),
    )
    return fig


def make_china_trade_chart(df: pd.DataFrame) -> go.Figure:
    work = df[df["metric"].isin(["Imports from China", "Exports to China"])].copy()
    work["flow_label"] = work["metric"].map(
        {
            "Imports from China": "United States imports from China",
            "Exports to China": "United States exports to China",
        }
    )
    fig = px.line(
        work,
        x="date",
        y="value",
        color="flow_label",
        title="United States-China trade flows",
        labels={"date": "Date", "value": "United States dollars<br>(millions)", "flow_label": "Trade flow"},
    )
    fig.update_layout(height=310, title_font_size=14, yaxis=dict(gridcolor="#e9edf3"), legend=dict(orientation="h", y=-0.34, x=0), margin=dict(l=62, r=14, t=50, b=78))
    return fig


def make_trade_balance_chart(df: pd.DataFrame) -> go.Figure:
    work = df[df["metric"] == "Trade Balance"].copy()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=work["date"],
            y=work["value"],
            mode="lines",
            fill="tozeroy",
            name="United States total trade balance",
            line=dict(color="#b15c63", width=2.4),
            hovertemplate="%{x|%Y-%m-%d}<br>Value: %{y:,.2f}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#667085", line_width=1)
    fig.update_layout(
        title="United States total trade balance",
        height=310,
        xaxis=dict(title="Date"),
        yaxis=dict(title="United States dollars<br>(millions)", gridcolor="#e9edf3"),
        title_font_size=14,
        margin=dict(l=62, r=14, t=50, b=34),
    )
    return fig


def make_currency_rate_chart(df: pd.DataFrame, tariff: pd.DataFrame, compact: bool = False) -> go.Figure:
    work = df.sort_values(["currency", "date"]).copy()
    selected_currencies = set(work["currency"].dropna().unique())
    selected_aliases = {
        currency: CURRENCY_TARIFF_ALIASES.get(currency, {currency})
        for currency in selected_currencies
    }

    fig = px.line(
        work,
        x="date",
        y="rate_vs_usd",
        color="currency",
        color_discrete_map=CURRENCY_COLOR_MAP,
        title="Currency rate versus United States dollar",
        labels={"date": "Date", "rate_vs_usd": "Local currency units<br>per United States dollar", "currency": "Currency"},
    )

    start_date = work["date"].min()
    end_date = work["date"].max()
    add_era_context_to_date_chart(
        fig,
        start_date,
        end_date,
        label_y=0.98 if compact else 1.07,
        short_label_y=0.98 if compact else 1.08,
    )

    tariff_events = tariff[(tariff["date"] >= start_date) & (tariff["date"] <= end_date)].copy()
    target_marker_added = False
    imposing_marker_added = False
    selected_currency_set = set(work["currency"])

    for _, event in tariff_events.sort_values("date").iterrows():
        target_currencies = [
            currency
            for currency, aliases in selected_aliases.items()
            if currency in selected_currency_set
            and (event["target_country"] in aliases or event["target_country"] in BROAD_TARGETS)
        ]
        imposing_currencies = [
            currency
            for currency, aliases in selected_aliases.items()
            if currency in selected_currency_set and event["imposing_country"] in aliases
        ]

        for currency in target_currencies:
            series = work[(work["currency"] == currency) & (work["date"] <= event["date"])]
            if series.empty:
                continue
            y_pos = series.iloc[-1]["rate_vs_usd"]
            fig.add_trace(
                go.Scatter(
                    x=[event["date"]],
                    y=[y_pos],
                    mode="markers+text",
                    marker=dict(symbol="triangle-up", size=10 if compact else 12, color="#ff2b2b", line=dict(width=1, color="#b00020")),
                    text=[f"{event['tariff_rate_pct']:.0f}%"],
                    textposition="top right",
                    textfont=dict(size=8 if compact else 10, color="#6b1f1f"),
                    name="Targeted by tariff" if not target_marker_added else None,
                    showlegend=not target_marker_added,
                    hovertemplate=(
                        "Targeted by tariff<br>"
                        f"Currency: {currency}<br>"
                        "Date: %{x|%Y-%m-%d}<br>"
                        f"Imposing: {event['imposing_country']}<br>"
                        f"Target: {event['target_country']}<br>"
                        f"Rate: {event['tariff_rate_pct']:.0f}%<br>"
                        f"Sector: {event['sector']}<extra></extra>"
                    ),
                )
            )
            target_marker_added = True

        for currency in imposing_currencies:
            series = work[(work["currency"] == currency) & (work["date"] <= event["date"])]
            if series.empty:
                continue
            y_pos = series.iloc[-1]["rate_vs_usd"]
            fig.add_trace(
                go.Scatter(
                    x=[event["date"]],
                    y=[y_pos],
                    mode="markers+text",
                    marker=dict(symbol="triangle-up", size=10 if compact else 12, color="#1f77d0", line=dict(width=1, color="#0b4f9c")),
                    text=[f"{event['tariff_rate_pct']:.0f}%"],
                    textposition="bottom right",
                    textfont=dict(size=8 if compact else 10, color="#0b3d78"),
                    name="Imposed tariff" if not imposing_marker_added else None,
                    showlegend=not imposing_marker_added,
                    hovertemplate=(
                        "Imposed tariff<br>"
                        f"Currency: {currency}<br>"
                        "Date: %{x|%Y-%m-%d}<br>"
                        f"Imposing: {event['imposing_country']}<br>"
                        f"Target: {event['target_country']}<br>"
                        f"Rate: {event['tariff_rate_pct']:.0f}%<br>"
                        f"Sector: {event['sector']}<extra></extra>"
                    ),
                )
            )
            imposing_marker_added = True

    if compact:
        fig.update_layout(
            height=320,
            title_font_size=13,
            yaxis=dict(gridcolor="#e9edf3"),
            legend=dict(
                orientation="h",
                y=-0.30,
                x=0,
                font=dict(size=10),
                title=dict(text="Currency", font=dict(size=10)),
            ),
            margin=dict(l=62, r=8, t=44, b=82),
        )
        fig.update_xaxes(
            title="Date",
            tickfont=dict(size=10),
            range=[
                start_date - pd.Timedelta(days=140),
                end_date + pd.Timedelta(days=100),
            ],
        )
        fig.update_yaxes(
            title="Local currency units<br>per United States dollar",
            title_font=dict(size=11),
            tickfont=dict(size=10),
        )
        return fig
    fig.update_layout(height=430, title_font_size=14, yaxis=dict(gridcolor="#e9edf3"), legend=dict(orientation="h", y=-0.24, x=0), margin=dict(l=70, r=14, t=54, b=70))
    return fig


def make_rolling_volatility_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df,
        x="date",
        y="rolling_7d_vol",
        color="currency",
        color_discrete_map=CURRENCY_COLOR_MAP,
        title="Rolling 7-day currency volatility",
        labels={"date": "Date", "rolling_7d_vol": "Volatility", "currency": "Currency"},
    )
    fig.update_layout(height=310, title_font_size=14, yaxis=dict(gridcolor="#e9edf3"), legend=dict(orientation="h", y=-0.32, x=0), margin=dict(l=50, r=14, t=50, b=74))
    return fig


def make_currency_event_change_chart(df: pd.DataFrame) -> go.Figure:
    work = df.dropna(subset=["pct_change_1d"]).copy()
    work["Event proximity"] = work["tariff_event_nearby"].map({True: "Near tariff event", False: "Not near event"})
    fig = px.box(
        work,
        x="Event proximity",
        y="pct_change_1d",
        color="currency",
        color_discrete_map=CURRENCY_COLOR_MAP,
        title="One-day currency change near tariff events",
        labels={"pct_change_1d": "One-day change (%)", "currency": "Currency"},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#667085", line_width=1)
    fig.update_layout(height=310, title_font_size=14, yaxis=dict(gridcolor="#e9edf3"), legend=dict(orientation="h", y=-0.32, x=0), margin=dict(l=54, r=14, t=50, b=74))
    return fig


def render_inflation_currency_tab() -> None:
    inflation = load_inflation_data(INFLATION_PATH)
    currency = load_currency_data(CURRENCY_PATH)
    tariff = load_tariff_data(TARIFF_PATH)

    st.markdown(
        """
        <style>
        .page5-page-title {
            margin-top: -0.7rem;
            margin-bottom: 0.35rem;
            padding-bottom: 0.28rem;
        }
        .page5-compact-title h1 {
            font-size: 1.35rem;
            line-height: 1.2;
            margin: 0;
        }
        .page5-compact-title p {
            margin: 0;
            color: #667085;
            font-size: 0.82rem;
            line-height: 1.15;
        }
        .page5-kpis {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.7rem;
            margin: 0.35rem 0 0.85rem;
        }
        .page5-kpi {
            border: 1px solid #d9dee7;
            border-top: 3px solid #20242a;
            background: #f7f9fb;
            border-radius: 6px;
            padding: 0.8rem 0.65rem 0.7rem;
            min-width: 0;
            min-height: 92px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            text-align: center;
        }
        .page5-kpi strong {
            display: block;
            font-size: 1.25rem;
            font-weight: 700;
            line-height: 1.15;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            order: 1;
        }
        .page5-kpi span {
            display: block;
            color: #667085;
            font-size: 0.68rem;
            line-height: 1.1;
            margin-top: 0.35rem;
            text-transform: uppercase;
            letter-spacing: 0.45px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            order: 2;
        }
        .page5-kpi::after {
            content: "";
            width: 28px;
            height: 3px;
            border-radius: 2px;
            background: currentColor;
            margin: 0.45rem auto 0;
            order: 3;
        }
        </style>
        <div class="page-title page5-page-title">
            <div class="page5-compact-title">
                <h1>Inflation & Currency Response</h1>
                <p>Connecting tariff tension to United States price pressure, United States-China trade flows, the United States total trade balance, and exchange-rate stress.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    inflation_all, metric_filtered, currency_filtered, selected_metrics = filter_inflation_currency_data(
        inflation,
        currency,
    )

    if inflation_all.empty and currency_filtered.empty:
        st.warning("No rows match the current filters.")
        return

    latest_cpi = (
        inflation_all[(inflation_all["metric"] == "CPI") & (inflation_all["category"] == "All Items")]
        .dropna(subset=["yoy_change_pct"])
        .sort_values("date")
        .tail(1)
    )
    latest_import_price = (
        inflation_all[inflation_all["metric"] == "Import Price Index"]
        .dropna(subset=["yoy_change_pct"])
        .sort_values("date")
        .tail(1)
    )
    latest_trade_balance = (
        inflation_all[inflation_all["metric"] == "Trade Balance"]
        .dropna(subset=["value"])
        .sort_values("date")
        .tail(1)
    )
    event_rows = int(currency_filtered["tariff_event_nearby"].sum()) if not currency_filtered.empty else 0

    render_kpi_row(
        [
            (
                "Latest United States CPI YoY",
                format_pct(latest_cpi.iloc[0]["yoy_change_pct"]) if not latest_cpi.empty else "n/a",
                "#20242a",
            ),
            (
                "Latest United States import price YoY",
                format_pct(latest_import_price.iloc[0]["yoy_change_pct"]) if not latest_import_price.empty else "n/a",
                PAGE5_BLUE,
            ),
            (
                "Latest United States total trade balance",
                format_usd_millions_as_billions(latest_trade_balance.iloc[0]["value"]) if not latest_trade_balance.empty else "n/a",
                PAGE5_ORANGE,
            ),
            ("Currency rows near tariff events", f"{event_rows:,}", PAGE5_GREEN),
        ]
    )

    price_response = inflation_all[
        ((inflation_all["metric"] == "CPI") & (inflation_all["category"] == "All Items"))
        | (inflation_all["metric"].isin(["PPI", "PCE"]))
    ]
    left_panel, right_panel = st.columns(2, gap="large")
    with left_panel:
        st.subheader("United States price and trade channel")
        price_left, price_right = st.columns(2)
        with price_left:
            if price_response.empty:
                st.info("No United States CPI/PPI/PCE rows match the current metric, era, and date filters.")
            else:
                st.plotly_chart(
                    make_price_response_chart(inflation_all, compact=True),
                    use_container_width=True,
                    config=PLOTLY_CONFIG,
                    key="page5_price_response_chart",
                )
        with price_right:
            if metric_filtered.empty:
                st.info("No selected metric rows match the current filters.")
            else:
                st.plotly_chart(
                    make_average_yoy_by_era_chart(metric_filtered, compact=True),
                    use_container_width=True,
                    config=PLOTLY_CONFIG,
                    key="page5_average_yoy_by_era_chart",
                )

        trade_left, trade_right = st.columns(2)
        with trade_left:
            if inflation_all[inflation_all["metric"].isin(["Imports from China", "Exports to China"])].empty:
                st.info("No United States-China import/export rows match the current filters.")
            else:
                st.plotly_chart(
                    make_china_trade_chart(inflation_all),
                    use_container_width=True,
                    config=PLOTLY_CONFIG,
                    key="page5_china_trade_chart",
                )
        with trade_right:
            if inflation_all[inflation_all["metric"] == "Trade Balance"].empty:
                st.info("No United States total trade balance rows match the current filters.")
            else:
                st.plotly_chart(
                    make_trade_balance_chart(inflation_all),
                    use_container_width=True,
                    config=PLOTLY_CONFIG,
                    key="page5_trade_balance_chart",
                )

    with right_panel:
        st.subheader("Exchange-rate response")
        if currency_filtered.empty:
            st.info("No selected-country currency rows match the current filters.")
        else:
            st.plotly_chart(
                make_currency_rate_chart(currency_filtered, tariff, compact=True),
                use_container_width=True,
                config=PLOTLY_CONFIG,
                key="page5_currency_rate_chart",
            )
            fx_left, fx_right = st.columns(2)
            with fx_left:
                st.plotly_chart(
                    make_rolling_volatility_chart(currency_filtered),
                    use_container_width=True,
                    config=PLOTLY_CONFIG,
                    key="page5_rolling_volatility_chart",
                )
            with fx_right:
                st.plotly_chart(
                    make_currency_event_change_chart(currency_filtered),
                    use_container_width=True,
                    config=PLOTLY_CONFIG,
                    key="page5_currency_event_change_chart",
                )

    with st.expander("Filtered data tables"):
        st.markdown("United States inflation, United States macro, and United States-China trade rows")
        st.dataframe(
            inflation_all.sort_values("date", ascending=False),
            width="stretch",
            hide_index=True,
            height=280,
        )
        st.markdown("Selected-country currency response rows")
        st.dataframe(
            currency_filtered.sort_values("date", ascending=False),
            width="stretch",
            hide_index=True,
            height=280,
        )

    st.markdown(
        f"""
        <div class="source-note">
            Sources: <code>{INFLATION_PATH}</code> and <code>{CURRENCY_PATH}</code>.
            Inflation data covers United States series, including United States-China trade rows and the United States total trade balance. Currency data covers selected countries/economies.
        </div>
        """,
        unsafe_allow_html=True,
    )
