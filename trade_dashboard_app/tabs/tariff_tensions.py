from __future__ import annotations

from html import escape

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


def _compact_figure(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        showlegend=False,
        margin=dict(l=6, r=6, t=48, b=24),
        title=dict(font=dict(size=13)),
        hovermode="closest",
    )
    fig.update_xaxes(title_font=dict(size=10), tickfont=dict(size=10))
    fig.update_yaxes(title_font=dict(size=10), tickfont=dict(size=10))
    fig.update_coloraxes(colorbar=dict(thickness=8, len=0.72, tickfont=dict(size=9), title_font=dict(size=9)))
    return fig


def _set_all_checkboxes(option_count: int, key_prefix: str) -> None:
    select_all = st.session_state.get(f"{key_prefix}_select_all", False)
    for idx in range(option_count):
        st.session_state[f"{key_prefix}_{idx}"] = select_all


def _sync_select_all(option_count: int, key_prefix: str) -> None:
    st.session_state[f"{key_prefix}_select_all"] = all(
        st.session_state.get(f"{key_prefix}_{idx}", False) for idx in range(option_count)
    )


def _checkbox_dropdown(label: str, options: list[str], default: list[str], key_prefix: str) -> list[str]:
    for idx, option in enumerate(options):
        st.session_state.setdefault(f"{key_prefix}_{idx}", option in default)
    st.session_state.setdefault(
        f"{key_prefix}_select_all",
        all(st.session_state.get(f"{key_prefix}_{idx}", False) for idx in range(len(options))),
    )

    selected = []
    selected_count = _selected_count(options, default, key_prefix)
    with st.popover(f"{label} ({selected_count})"):
        st.checkbox(
            "Select all",
            key=f"{key_prefix}_select_all",
            on_change=_set_all_checkboxes,
            args=(len(options), key_prefix),
        )
        for idx, option in enumerate(options):
            checked = st.checkbox(
                option,
                key=f"{key_prefix}_{idx}",
                on_change=_sync_select_all,
                args=(len(options), key_prefix),
            )
            if checked:
                selected.append(option)
    return selected


def _selected_count(options: list[str], default: list[str], key_prefix: str) -> int:
    return sum(1 for idx, option in enumerate(options) if st.session_state.get(f"{key_prefix}_{idx}", option in default))


def _country_color_map(countries: list[str]) -> dict[str, str]:
    palette = CVD_QUALITATIVE_COLORS
    return {country: palette[idx % len(palette)] for idx, country in enumerate(countries)}


def _render_country_legend(countries: list[str], color_map: dict[str, str]) -> None:
    items = "\n".join(
        f"""
        <span class="impact-country-legend-item">
            <span class="impact-country-legend-swatch" style="background:{escape(color_map[country])};"></span>
            <span>{escape(country)}</span>
        </span>
        """
        for country in countries
        if country in color_map
    )
    st.markdown(
        f"""
        <div class="impact-country-legend">
            <span class="impact-country-legend-title">Country colors</span>
            {items}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tariff_tensions_tab() -> None:
    macro = load_macro_data(DATA_PATH)
    years = sorted(macro["year"].dropna().astype(int).unique().tolist())
    country_options = sorted(macro["country"].dropna().unique())
    period_options = [p for p in PERIOD_ORDER if p in macro["period"].dropna().unique()]
    compact_height = 220

    st.markdown(
        """
        <style>
        .block-container {
            max-width: none !important;
            width: 100% !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-top: 3.5rem !important;
        }
        .page-title {
            margin-bottom: 0.45rem;
            padding-bottom: 0.35rem;
        }
        .impact-compact-title h1 {
            font-size: 1.35rem;
            margin: 0 0 0.1rem;
        }
        .impact-compact-title p {
            margin: 0;
            color: #667085;
            font-size: 0.82rem;
        }
        div[data-testid="stMetric"] {
            padding: 0.45rem 0.6rem;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.05rem;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.72rem;
        }
        .impact-kpis {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.45rem;
            margin: 0.15rem 0 0.45rem;
        }
        .impact-kpi {
            border: 1px solid #d9dee7;
            background: #f7f9fb;
            border-radius: 6px;
            padding: 0.35rem 0.5rem;
            min-width: 0;
        }
        .impact-kpi span {
            display: block;
            color: #667085;
            font-size: 0.68rem;
            line-height: 1.05;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .impact-kpi strong {
            display: block;
            color: #20242a;
            font-size: 0.92rem;
            line-height: 1.15;
            margin-top: 0.1rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 0.35rem;
        }
        div[data-testid="stHorizontalBlock"] {
            gap: 0.55rem;
        }
        div[data-testid="stPlotlyChart"] {
            border: 1px solid #e5e9f0;
            border-radius: 6px;
            overflow: hidden;
        }
        .impact-country-legend {
            display: flex;
            align-items: center;
            gap: 0.45rem 0.75rem;
            flex-wrap: wrap;
            border: 1px solid #e5e9f0;
            border-radius: 6px;
            background: #ffffff;
            padding: 0.34rem 0.55rem;
            margin: -0.05rem 0 0.1rem;
            min-height: 1.85rem;
        }
        .impact-country-legend-title {
            color: #667085;
            font-size: 0.72rem;
            font-weight: 600;
            margin-right: 0.2rem;
        }
        .impact-country-legend-item {
            display: inline-flex;
            align-items: center;
            gap: 0.28rem;
            color: #20242a;
            font-size: 0.72rem;
            line-height: 1;
            white-space: nowrap;
        }
        .impact-country-legend-swatch {
            width: 0.62rem;
            height: 0.62rem;
            border-radius: 50%;
            border: 1px solid rgba(32,36,42,0.18);
            flex: 0 0 auto;
        }
        </style>
        <div class="page-title">
            <div class="impact-compact-title">
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
    c1, c2, c3, c4, c5, c6, c7 = st.columns([1.0, 0.92, 0.9, 0.72, 1.0, 0.62, 0.85])
    with c1:
        selected_countries = _checkbox_dropdown(
            "Countries",
            country_options,
            default_countries or country_options[:6],
            "impact_country",
        )
    with c2:
        selected_periods = _checkbox_dropdown(
            "Periods",
            period_options,
            period_options,
            "impact_period",
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
    with c4:
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
    with c5:
        yoy_indicator = st.selectbox(
            "YoY indicator",
            yoy_indicator_options,
            index=yoy_indicator_options.index(EXPORTS) if EXPORTS in yoy_indicator_options else 0,
            key="impact_yoy_indicator",
        )
    with c6:
        robust_yoy_display = st.checkbox(
            "Robust YoY",
            value=True,
            key="impact_robust_yoy_scale",
        )
    with c7:
        fdi_display_mode = st.selectbox(
            "FDI display",
            ["Absolute USD", "Indexed to 100"],
            index=0,
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
    country_color_map = _country_color_map(selected_countries)

    st.markdown(
        f"""
        <div class="impact-kpis">
            <div class="impact-kpi"><span>Countries</span><strong>{len(selected_countries)}</strong></div>
            <div class="impact-kpi"><span>{_metric_label("Trade value", trade_year)}</span><strong>{_metric_value(latest_trade, format_usd)}</strong></div>
            <div class="impact-kpi"><span>{_metric_label("Avg trade/GDP", trade_gdp_year)}</span><strong>{_metric_value(avg_trade_gdp, format_pct_plain)}</strong></div>
            <div class="impact-kpi"><span>{_metric_label("FDI inflows", fdi_year)}</span><strong>{_metric_value(latest_fdi, format_usd)}</strong></div>
            <div class="impact-kpi"><span>{_metric_label("Average GDP growth", gdp_growth_year)}</span><strong>{_metric_value(avg_gdp_growth, format_pct_plain)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_left, top_mid, top_right = st.columns(3)
    with top_left:
        st.plotly_chart(
            _compact_figure(
                make_trade_import_export_chart(
                    filtered,
                    selected_trade_flow,
                    height=compact_height,
                    country_color_map=country_color_map,
                )
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with top_mid:
        st.plotly_chart(
            _compact_figure(
                make_trade_gdp_chart(
                    filtered,
                    height=compact_height,
                    country_color_map=country_color_map,
                )
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with top_right:
        st.plotly_chart(
            _compact_figure(
                make_fdi_inflows_chart(
                    filtered,
                    fdi_display_mode,
                    height=compact_height,
                    country_color_map=country_color_map,
                )
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    _render_country_legend(selected_countries, country_color_map)

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        if yoy_indicator:
            st.plotly_chart(
                _compact_figure(
                    make_yoy_change_by_period_chart(
                        filtered,
                        [yoy_indicator],
                        robust_yoy_display,
                        height=compact_height,
                    )
                ),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        else:
            st.info("Select at least one YoY indicator.")
    with bottom_right:
        st.plotly_chart(
            _compact_figure(make_gdp_growth_period_chart(filtered, height=compact_height)),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with st.expander("Notes and source", expanded=False):
        st.caption(
            "Robust YoY clips displayed values to the 5th-95th percentile for readability; original values remain in tooltips. "
            f"Source: {DATA_PATH}."
        )
