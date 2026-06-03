from core import *

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

