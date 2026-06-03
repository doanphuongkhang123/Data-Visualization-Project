from core import *

def render_sector_impact_tab() -> None:
    df = load_sector_data(SECTOR_PATH)
    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Sectoral Impact</h1>
                <p>Sector ETF performance and volatility by country and tariff sensitivity.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    base = filter_by_date(df, "sector")
    c1, c2, c3 = st.columns([0.85, 1.25, 0.9])
    with c1:
        countries = sorted(base["country"].dropna().unique())
        selected_countries = st.multiselect("Countries", countries, default=countries, key="sector_countries")
    with c2:
        sectors = sorted(base[base["country"].isin(selected_countries)]["sector"].dropna().unique())
        selected_sectors = st.multiselect("Sectors", sectors, default=sectors, key="sector_names")
    with c3:
        sensitivities = sorted(base["tariff_sensitivity"].dropna().unique())
        selected_sensitivities = st.multiselect(
            "Tariff sensitivity",
            sensitivities,
            default=sensitivities,
            key="sector_sensitivities",
        )

    filtered = base[
        base["country"].isin(selected_countries)
        & base["sector"].isin(selected_sectors)
        & base["tariff_sensitivity"].isin(selected_sensitivities)
    ].copy()
    if filtered.empty:
        st.warning("No sector data match the current filters.")
        return

    latest = make_latest_table(filtered, ["country", "sector"])
    best = latest.sort_values("indexed_to_100", ascending=False).iloc[0]
    worst = latest.sort_values("indexed_to_100", ascending=True).iloc[0]
    high_share = (latest["tariff_sensitivity"] == "High").mean() * 100

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Sector-country pairs", f"{len(latest):,}")
    k2.metric("Best latest sector", best["sector_label"], f"{best['indexed_to_100']:.1f}")
    k3.metric("Weakest latest sector", worst["sector_label"], f"{worst['indexed_to_100']:.1f}")
    k4.metric("High-sensitivity share", f"{high_share:.1f}%")

    st.plotly_chart(make_sector_performance_chart(filtered))
    left, right = st.columns(2)
    with left:
        st.plotly_chart(make_sector_latest_heatmap(filtered))
    with right:
        st.plotly_chart(make_sector_return_distribution(filtered))
    st.plotly_chart(make_sector_volatility_bar(filtered))

    st.markdown(
        f"""
        <div class="source-note">
            Source: <code>{SECTOR_PATH}</code>. Sector data covers USA, China, and global ETFs.
        </div>
        """,
        unsafe_allow_html=True,
    )

