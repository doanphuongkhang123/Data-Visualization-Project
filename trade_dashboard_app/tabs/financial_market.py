from core import *

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

