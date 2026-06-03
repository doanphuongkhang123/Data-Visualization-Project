from core import *

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

