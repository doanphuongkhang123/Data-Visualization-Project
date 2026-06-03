from __future__ import annotations

from core import *


def _metric_value(value: float, formatter) -> str:
    if pd.isna(value):
        return "No data"
    return formatter(value)


def _metric_label(base: str, year: int | None) -> str:
    return f"{base}, {year}" if year is not None else f"{base}, latest year"


def _missing_selected_periods(df: pd.DataFrame, selected_periods: list[str], indicators: list[str]) -> list[str]:
    available_periods = set(
        df[df["indicator_name"].isin(indicators) & df["value"].notna()]["period"].dropna().unique()
    )
    return [period for period in selected_periods if period not in available_periods]


def render_tariff_tensions_tab() -> None:
    macro = load_macro_data(DATA_PATH)
    years = sorted(macro["year"].dropna().astype(int).unique().tolist())
    country_options = sorted(macro["country"].dropna().unique())
    period_options = [p for p in PERIOD_ORDER if p in macro["period"].dropna().unique()]

    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Trade and Macro Impact</h1>
                <p>Annual trade flows, YoY shifts, GDP exposure, growth, and FDI across trade-war periods.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    default_countries = [
        c
        for c in ["USA", "China", "Vietnam", "Germany", "Mexico"]
        if c in country_options
    ]
    c1, c2, c3 = st.columns([1.35, 1.25, 0.9])
    with c1:
        selected_countries = st.multiselect(
            "Countries",
            country_options,
            default=default_countries or country_options[:6],
            key="impact_countries",
        )
    with c2:
        selected_periods = st.multiselect(
            "Periods",
            period_options,
            default=period_options,
            key="impact_periods",
        )
    with c3:
        selected_year_range = st.slider(
            "Year range",
            min_value=min(years),
            max_value=max(years),
            value=(min(years), max(years)),
            step=1,
            key="impact_year_range",
        )

    flow_col, yoy_col, scale_col, fdi_col = st.columns([0.9, 1.25, 0.85, 0.95])
    with flow_col:
        selected_trade_flow = st.selectbox(
            "Trade flow",
            ["Exports", "Imports"],
            index=0,
            key="impact_trade_flow",
        )

    yoy_indicator_options = [
        EXPORTS,
        IMPORTS,
        TRADE_GDP,
        GDP_GROWTH,
        FDI_INFLOW,
    ]
    yoy_indicator_options = [i for i in yoy_indicator_options if i in macro["indicator_name"].unique()]
    with yoy_col:
        yoy_indicator = st.selectbox(
            "YoY indicator",
            yoy_indicator_options,
            index=yoy_indicator_options.index(EXPORTS) if EXPORTS in yoy_indicator_options else 0,
            key="impact_yoy_indicator",
        )
    with scale_col:
        robust_yoy_display = st.checkbox(
            "Robust YoY scale",
            value=True,
            key="impact_robust_yoy_scale",
        )
    with fdi_col:
        fdi_display_mode = st.radio(
            "FDI display",
            ["Absolute USD", "Indexed to 100"],
            horizontal=True,
            key="impact_fdi_display_mode",
        )

    if not selected_countries or not selected_periods:
        st.warning("Select at least one country and one period.")
        return

    filtered = filter_annual_macro(macro, selected_countries, selected_periods, selected_year_range)
    if filtered.empty:
        st.warning("No data available for the selected filters.")
        return
    visible_indicators = [EXPORTS, IMPORTS, TRADE_GDP, GDP_GROWTH, FDI_INFLOW]
    missing_periods = _missing_selected_periods(filtered, selected_periods, visible_indicators)
    if missing_periods:
        st.caption(
            "Some selected periods have no available observations for the displayed trade and macro indicators: "
            f"{', '.join(missing_periods)}."
        )

    trade_indicator = EXPORTS if selected_trade_flow == "Exports" else IMPORTS
    latest_trade, trade_year = latest_indicator_snapshot(filtered, trade_indicator, "sum")
    avg_trade_gdp, trade_gdp_year = latest_indicator_snapshot(filtered, TRADE_GDP, "mean")
    latest_fdi, fdi_year = latest_indicator_snapshot(filtered, FDI_INFLOW, "sum")
    avg_gdp_growth, gdp_growth_year = latest_indicator_snapshot(filtered, GDP_GROWTH, "mean")

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Countries", f"{len(selected_countries)}")
    k2.metric(_metric_label("Trade value", trade_year), _metric_value(latest_trade, format_usd))
    k3.metric(_metric_label("Avg trade/GDP", trade_gdp_year), _metric_value(avg_trade_gdp, format_pct_plain))
    k4.metric(_metric_label("FDI inflows", fdi_year), _metric_value(latest_fdi, format_usd))
    k5.metric(_metric_label("Average GDP growth", gdp_growth_year), _metric_value(avg_gdp_growth, format_pct_plain))

    st.plotly_chart(make_trade_import_export_chart(filtered, selected_trade_flow))

    left, right = st.columns(2)
    with left:
        if yoy_indicator:
            st.plotly_chart(make_yoy_change_by_period_chart(filtered, [yoy_indicator], robust_yoy_display))
            if robust_yoy_display:
                st.caption("YoY values are clipped to the 5th-95th percentile for readability. Original values remain available in tooltips.")
        else:
            st.info("Select at least one YoY indicator.")
    with right:
        st.plotly_chart(make_trade_gdp_chart(filtered))
        st.caption("Vietnam shows a much higher trade-to-GDP ratio than larger economies, indicating stronger exposure to global trade fluctuations.")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(make_gdp_growth_period_chart(filtered))
        st.caption("Average GDP growth helps compare macroeconomic performance across trade-war periods.")
    with right:
        st.plotly_chart(make_fdi_inflows_chart(filtered, fdi_display_mode))
        st.caption("FDI values are shown in current USD. Countries with larger economies may dominate the absolute scale.")

    if len(selected_countries) > 6:
        st.caption(
            "The GDP growth chart above is already shown as a country-by-period heatmap, so the separate macro performance heatmap is omitted to avoid duplicating the same view."
        )
    else:
        st.plotly_chart(make_macro_performance_heatmap(filtered), use_container_width=True)

    st.subheader("Period summary")
    summary = make_macro_period_summary_table(filtered)
    if summary.empty:
        st.warning("No data available for the selected filters.")
    else:
        display_summary = summary.copy()
        monetary_indicators = {EXPORTS, IMPORTS, FDI_INFLOW}
        percent_indicators = {TRADE_GDP, GDP_GROWTH}
        display_summary["Average value"] = display_summary.apply(
            lambda row: format_usd(row["average_value"])
            if row["indicator_name"] in monetary_indicators
            else format_pct_plain(row["average_value"])
            if row["indicator_name"] in percent_indicators
            else f"{row['average_value']:.2f}",
            axis=1,
        )
        display_summary["Median YoY %"] = display_summary["median_yoy_change_pct"].map(format_pct_plain)
        display_summary["Observations"] = display_summary["observations"].astype(int)
        display_summary = display_summary.rename(
            columns={
                "period": "Period",
                "indicator_label": "Indicator",
            }
        )[["Period", "Indicator", "Average value", "Median YoY %", "Observations"]]
        display_summary["Period"] = display_summary["Period"].astype(str)
        st.dataframe(
            display_summary,
            use_container_width=True,
            hide_index=True,
            height=360,
        )

    st.markdown(
        f"""
        <div class="source-note">
            Source: <code>{DATA_PATH}</code>. The tab uses annual observations for exports/imports,
            YoY change, trade as a share of GDP, GDP growth, and FDI net inflows.
        </div>
        """,
        unsafe_allow_html=True,
    )
