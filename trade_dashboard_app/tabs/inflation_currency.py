from core import *


DEFAULT_METRICS = ["CPI", "PPI", "PCE", "Import Price Index"]
DEFAULT_COUNTRIES = ["USA", "China", "European Union", "Japan", "South Korea", "Vietnam"]
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


def format_usd_millions_as_billions(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value) / 1_000:,.1f}B"


def filter_inflation_currency_data(inflation: pd.DataFrame, currency: pd.DataFrame):
    min_date = min(inflation["date"].min(), currency["date"].min()).date()
    max_date = max(inflation["date"].max(), currency["date"].max()).date()

    c1, c2, c3 = st.columns([1.2, 1.25, 1.25])
    with c1:
        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="page5_date_range",
        )
    with c2:
        metric_options = sorted(inflation["metric"].dropna().unique())
        selected_metrics = st.multiselect(
            "Metric",
            metric_options,
            default=[m for m in DEFAULT_METRICS if m in metric_options],
            key="page5_metrics",
        )
    with c3:
        era_options = [era for era in ERA_ORDER if era in set(inflation["era"].dropna())]
        selected_eras = st.multiselect("Era", era_options, default=era_options, key="page5_eras")

    c4, c5 = st.columns([1.25, 1.25])
    country_options = sorted(set(currency["country"].dropna()) | set(inflation["country"].dropna()))
    default_countries = [country for country in DEFAULT_COUNTRIES if country in country_options]
    with c4:
        selected_countries = st.multiselect(
            "Country / economy",
            country_options,
            default=default_countries or country_options,
            key="page5_countries",
        )

    currency_base = currency[currency["country"].isin(selected_countries)]
    currency_options = sorted(currency_base["currency"].dropna().unique())
    with c5:
        selected_currencies = st.multiselect(
            "Currency",
            currency_options,
            default=currency_options,
            key="page5_currencies",
        )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start_date, end_date = pd.to_datetime(min_date), pd.to_datetime(max_date)

    inflation_filtered = inflation[
        (inflation["date"] >= start_date)
        & (inflation["date"] <= end_date)
        & (inflation["country"].isin(selected_countries))
        & (inflation["era"].isin(selected_eras))
    ].copy()

    currency_filtered = currency[
        (currency["date"] >= start_date)
        & (currency["date"] <= end_date)
        & (currency["country"].isin(selected_countries))
        & (currency["currency"].isin(selected_currencies))
    ].copy()

    metric_filtered = inflation_filtered[inflation_filtered["metric"].isin(selected_metrics)].copy()
    return inflation_filtered, metric_filtered, currency_filtered, selected_metrics


def make_price_response_chart(df: pd.DataFrame) -> go.Figure:
    core = df[
        ((df["metric"] == "CPI") & (df["category"] == "All Items"))
        | (df["metric"].isin(["PPI", "PCE"]))
    ].copy()
    core["display_metric"] = core["metric"].map(
        {
            "CPI": "US CPI - All Items",
            "PPI": "US PPI",
            "PCE": "US PCE",
        }
    )
    fig = px.line(
        core,
        x="date",
        y="value",
        color="display_metric",
        facet_row="display_metric",
        title="US CPI - All Items, US PPI, and US PCE over time",
        labels={"date": "", "value": "US index/value", "display_metric": "US price metric"},
    )
    fig.update_yaxes(matches=None, gridcolor="#e9edf3")
    fig.for_each_annotation(lambda a: a.update(text=a.text.replace("display_metric=", "")))
    fig.update_layout(height=560, showlegend=False)
    return fig


def make_import_price_chart(df: pd.DataFrame) -> go.Figure:
    work = df[df["metric"] == "Import Price Index"].copy()
    fig = px.line(
        work,
        x="date",
        y="value",
        color="series_label",
        title="US import price index over time",
        labels={"date": "", "value": "US import price index/value", "series_label": ""},
    )
    fig.update_layout(height=430, yaxis=dict(gridcolor="#e9edf3"), showlegend=False)
    return fig


def make_average_yoy_by_era_chart(df: pd.DataFrame) -> go.Figure:
    work = df.dropna(subset=["yoy_change_pct"]).copy()
    avg = work.groupby(["era", "metric"], as_index=False)["yoy_change_pct"].mean()
    fig = px.bar(
        avg,
        x="era",
        y="yoy_change_pct",
        color="metric",
        barmode="group",
        category_orders={"era": ERA_ORDER},
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="US average YoY change by selected metric and era",
        labels={"era": "Trade-war era", "yoy_change_pct": "US average YoY change (%)", "metric": "US metric"},
    )
    fig.update_layout(height=430, yaxis=dict(gridcolor="#e9edf3"), legend=dict(orientation="h", y=-0.28, x=0))
    return fig


def make_china_trade_chart(df: pd.DataFrame) -> go.Figure:
    work = df[df["metric"].isin(["Imports from China", "Exports to China"])].copy()
    work["flow_label"] = work["metric"].map(
        {
            "Imports from China": "US imports from China",
            "Exports to China": "US exports to China",
        }
    )
    fig = px.line(
        work,
        x="date",
        y="value",
        color="flow_label",
        title="US imports from China vs US exports to China",
        labels={"date": "", "value": "US trade value (USD millions)", "flow_label": "US-China flow"},
    )
    fig.update_layout(height=430, yaxis=dict(gridcolor="#e9edf3"), legend=dict(orientation="h", y=-0.22, x=0))
    return fig


def make_china_trade_yoy_chart(df: pd.DataFrame) -> go.Figure:
    work = df[
        df["metric"].isin(["Imports from China", "Exports to China"])
        & df["yoy_change_pct"].notna()
    ].copy()
    work["flow_label"] = work["metric"].map(
        {
            "Imports from China": "US imports from China",
            "Exports to China": "US exports to China",
        }
    )
    fig = px.line(
        work,
        x="date",
        y="yoy_change_pct",
        color="flow_label",
        title="YoY change in US-China imports and exports",
        labels={"date": "", "yoy_change_pct": "US-China YoY change (%)", "flow_label": "US-China flow"},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#667085", line_width=1)
    fig.update_layout(height=380, yaxis=dict(gridcolor="#e9edf3"), legend=dict(orientation="h", y=-0.24, x=0))
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
            name="US total trade balance",
            line=dict(color="#b15c63", width=2.4),
            hovertemplate="%{x|%Y-%m-%d}<br>Value: %{y:,.2f}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#667085", line_width=1)
    fig.update_layout(
        title="US total trade balance over time",
        height=430,
        xaxis=dict(title=""),
        yaxis=dict(title="US trade balance (USD millions)", gridcolor="#e9edf3"),
    )
    return fig


def make_currency_rate_chart(df: pd.DataFrame, tariff: pd.DataFrame) -> go.Figure:
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
        title="Currency rate versus USD with tariff-event markers",
        labels={"date": "", "rate_vs_usd": "Local currency units per USD", "currency": "Currency"},
    )

    start_date = work["date"].min()
    end_date = work["date"].max()
    if pd.notna(start_date) and pd.notna(end_date):
        trade_war_1_start = max(pd.Timestamp("2018-03-01"), start_date)
        trade_war_1_end = min(pd.Timestamp("2019-12-31"), end_date)
        if trade_war_1_start <= trade_war_1_end:
            fig.add_vrect(
                x0=trade_war_1_start,
                x1=trade_war_1_end,
                fillcolor="#d9895b",
                opacity=0.18,
                line_width=0,
                annotation_text="Trade War 1.0",
                annotation_position="top left",
            )

        trade_war_2_start = max(pd.Timestamp("2024-01-01"), start_date)
        if trade_war_2_start <= end_date:
            fig.add_vrect(
                x0=trade_war_2_start,
                x1=end_date,
                fillcolor="#b15c63",
                opacity=0.18,
                line_width=0,
                annotation_text="Trade War 2.0",
                annotation_position="top left",
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
                    marker=dict(symbol="triangle-up", size=12, color="#ff2b2b", line=dict(width=1, color="#b00020")),
                    text=[f"{event['tariff_rate_pct']:.0f}%"],
                    textposition="top right",
                    textfont=dict(size=10, color="#6b1f1f"),
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
                    marker=dict(symbol="triangle-up", size=12, color="#1f77d0", line=dict(width=1, color="#0b4f9c")),
                    text=[f"{event['tariff_rate_pct']:.0f}%"],
                    textposition="bottom right",
                    textfont=dict(size=10, color="#0b3d78"),
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

    fig.update_layout(height=560, yaxis=dict(gridcolor="#e9edf3"), legend=dict(orientation="h", y=-0.22, x=0))
    return fig


def make_rolling_volatility_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df,
        x="date",
        y="rolling_7d_vol",
        color="currency",
        title="Rolling 7-day currency volatility by selected country/economy",
        labels={"date": "", "rolling_7d_vol": "7-day volatility", "currency": "Currency"},
    )
    fig.update_layout(height=430, yaxis=dict(gridcolor="#e9edf3"), legend=dict(orientation="h", y=-0.24, x=0))
    return fig


def make_currency_event_change_chart(df: pd.DataFrame) -> go.Figure:
    work = df.dropna(subset=["pct_change_1d"]).copy()
    work["Event proximity"] = work["tariff_event_nearby"].map({True: "Near tariff event", False: "Not near event"})
    fig = px.box(
        work,
        x="Event proximity",
        y="pct_change_1d",
        color="currency",
        title="Currency change around tariff events by selected country/economy",
        labels={"pct_change_1d": "1-day change (%)", "currency": "Currency"},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#667085", line_width=1)
    fig.update_layout(height=430, yaxis=dict(gridcolor="#e9edf3"), legend=dict(orientation="h", y=-0.26, x=0))
    return fig


def make_currency_event_average_chart(df: pd.DataFrame) -> go.Figure:
    work = df.dropna(subset=["pct_change_1d"]).copy()
    work["abs_change_1d"] = work["pct_change_1d"].abs()
    avg = work.groupby(["currency", "tariff_event_nearby"], as_index=False)["abs_change_1d"].mean()
    avg["Event proximity"] = avg["tariff_event_nearby"].map({True: "Near tariff event", False: "Not near event"})
    fig = px.bar(
        avg,
        x="currency",
        y="abs_change_1d",
        color="Event proximity",
        barmode="group",
        title="Average absolute one-day currency move by event proximity",
        labels={"currency": "", "abs_change_1d": "Average absolute 1-day change (%)"},
        color_discrete_map={"Near tariff event": "#b15c63", "Not near event": "#4c78a8"},
    )
    fig.update_layout(height=430, yaxis=dict(gridcolor="#e9edf3"), legend=dict(orientation="h", y=-0.22, x=0))
    return fig


def make_latest_currency_pressure_chart(df: pd.DataFrame) -> go.Figure:
    latest = df.sort_values("date").groupby(["country", "currency"], as_index=False).tail(1)
    latest = latest.sort_values("pct_change_30d", ascending=False)
    fig = px.bar(
        latest,
        x="currency",
        y="pct_change_30d",
        color="country",
        title="Latest 30-day currency pressure by selected country/economy",
        labels={"currency": "", "pct_change_30d": "30-day change (%)", "country": "Country/economy"},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#667085", line_width=1)
    fig.update_layout(height=420, yaxis=dict(gridcolor="#e9edf3"), legend=dict(orientation="h", y=-0.24, x=0))
    return fig


def render_inflation_currency_tab() -> None:
    inflation = load_inflation_data(INFLATION_PATH)
    currency = load_currency_data(CURRENCY_PATH)
    tariff = load_tariff_data(TARIFF_PATH)

    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Inflation & Currency Response</h1>
                <p>Connecting tariff tension to US price pressure, US-China trade flows, the US total trade balance, and selected-country exchange-rate stress.</p>
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

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Latest US CPI YoY", format_pct(latest_cpi.iloc[0]["yoy_change_pct"]) if not latest_cpi.empty else "n/a")
    k2.metric(
        "Latest US import price YoY",
        format_pct(latest_import_price.iloc[0]["yoy_change_pct"]) if not latest_import_price.empty else "n/a",
    )
    k3.metric(
        "Latest US total trade balance",
        format_usd_millions_as_billions(latest_trade_balance.iloc[0]["value"]) if not latest_trade_balance.empty else "n/a",
    )
    k4.metric("Selected-country FX rows near tariff events", f"{event_rows:,}")

    st.subheader("US price pressure")
    price_response = inflation_all[
        ((inflation_all["metric"] == "CPI") & (inflation_all["category"] == "All Items"))
        | (inflation_all["metric"].isin(["PPI", "PCE"]))
    ]
    if price_response.empty:
        st.info("No US CPI/PPI/PCE rows match the current country/economy, era, and date filters.")
    else:
        st.plotly_chart(make_price_response_chart(inflation_all))

    left, right = st.columns(2)
    with left:
        if inflation_all[inflation_all["metric"] == "Import Price Index"].empty:
            st.info("No US import price index rows match the current filters.")
        else:
            st.plotly_chart(make_import_price_chart(inflation_all))
    with right:
        if metric_filtered.empty:
            st.info("No selected metric rows match the current filters.")
        else:
            st.plotly_chart(make_average_yoy_by_era_chart(metric_filtered))

    st.subheader("US-China trade and US total trade balance")
    st.caption("Left: US bilateral goods trade with China. Right: US total goods and services trade balance with all trading partners.")
    left, right = st.columns(2)
    with left:
        if inflation_all[inflation_all["metric"].isin(["Imports from China", "Exports to China"])].empty:
            st.info("No US-China import/export rows match the current filters.")
        else:
            st.plotly_chart(make_china_trade_chart(inflation_all))
    with right:
        if inflation_all[inflation_all["metric"] == "Trade Balance"].empty:
            st.info("No US total trade balance rows match the current filters.")
        else:
            st.plotly_chart(make_trade_balance_chart(inflation_all))

    trade_yoy = inflation_all[
        inflation_all["metric"].isin(["Imports from China", "Exports to China"])
        & inflation_all["yoy_change_pct"].notna()
    ]
    if trade_yoy.empty:
        st.info("No US-China import/export YoY rows match the current filters.")
    else:
        st.plotly_chart(make_china_trade_yoy_chart(inflation_all))

    st.subheader("Selected-country exchange-rate response")
    st.caption(
        "This section uses the selected currencies/countries from currency_impact.csv. "
        "Red triangles mark dates when the selected country/economy was targeted by a tariff; "
        "blue triangles mark dates when it imposed a tariff on others."
    )
    if currency_filtered.empty:
        st.info("No selected-country currency rows match the current filters.")
    else:
        st.plotly_chart(make_currency_rate_chart(currency_filtered, tariff))
        left, right = st.columns(2)
        with left:
            st.plotly_chart(make_rolling_volatility_chart(currency_filtered))
        with right:
            st.plotly_chart(make_currency_event_change_chart(currency_filtered))
        left, right = st.columns(2)
        with left:
            st.plotly_chart(make_currency_event_average_chart(currency_filtered))
        with right:
            st.plotly_chart(make_latest_currency_pressure_chart(currency_filtered))

    with st.expander("Filtered data tables"):
        st.markdown("US inflation, US macro, and US-China trade rows")
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
            Inflation data covers US series, including US-China trade rows and US total trade balance. Currency data covers selected countries/economies.
        </div>
        """,
        unsafe_allow_html=True,
    )
