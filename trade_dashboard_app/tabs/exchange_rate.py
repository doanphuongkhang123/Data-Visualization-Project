from core import *

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

