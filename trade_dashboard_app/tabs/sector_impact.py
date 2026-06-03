from core import *

def render_sector_impact_tab() -> None:
    df = load_sector_data(SECTOR_PATH)
    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Sectoral Impact</h1>
                <p>Identify sectors most affected by tariff uncertainty and observe how sensitivity relates to volatility.</p>
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
        sectors = sorted(base[base["country"].isin(selected_countries)]["sector_label"].dropna().unique())
        preferred = [
            "Technology (USA)",
            "Industrials (USA)",
            "Semiconductors (USA)",
            "Steel/Metals (USA)",
        ]
        default_sectors = [sector for sector in preferred if sector in sectors]
        if not default_sectors:
            default_sectors = sectors[:4]
        selected_sectors = st.multiselect("Sectors", sectors, default=default_sectors, key="sector_labels")
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
        & base["sector_label"].isin(selected_sectors)
        & base["tariff_sensitivity"].isin(selected_sensitivities)
    ].copy()
    if filtered.empty:
        st.warning("No sector data match the current filters.")
        return

    vol_work = filtered.dropna(subset=["volatility_10d"]).copy()
    ret_work = filtered.dropna(subset=["daily_return_pct"]).copy()
    if not vol_work.empty:
        avg_vol = (
            vol_work.groupby("sector_label", as_index=False)
            .agg(avg_volatility=("volatility_10d", "mean"))
            .sort_values("avg_volatility", ascending=False)
        )
        top_vol = avg_vol.iloc[0]
    else:
        top_vol = None
    if not ret_work.empty:
        avg_ret = (
            ret_work.groupby("sector_label", as_index=False)
            .agg(avg_return=("daily_return_pct", "mean"))
            .sort_values("avg_return", ascending=True)
        )
        low_ret = avg_ret.iloc[0]
    else:
        low_ret = None

    if not vol_work.empty:
        sensitivity_order = ["High", "Medium", "Low"]
        vol_by_sens = (
            vol_work.groupby("tariff_sensitivity", as_index=False)
            .agg(avg_volatility=("volatility_10d", "mean"))
        )
        if vol_by_sens.empty:
            vol_summary = "N/A"
            compare_note = "Insufficient data to compare High, Medium, and Low sensitivity."
        else:
            vol_by_sens["order"] = vol_by_sens["tariff_sensitivity"].map(
                {label: idx for idx, label in enumerate(sensitivity_order)}
            )
            vol_by_sens = vol_by_sens.sort_values("order")
            vol_map = dict(zip(vol_by_sens["tariff_sensitivity"], vol_by_sens["avg_volatility"]))
            vol_summary = ", ".join(
                f"{row.tariff_sensitivity}: {row.avg_volatility:.2f}"
                for row in vol_by_sens.itertuples()
            )
            if all(label in vol_map for label in ["High", "Medium", "Low"]):
                high_is_higher = vol_map["High"] > vol_map["Medium"] and vol_map["High"] > vol_map["Low"]
                compare_note = (
                    "High sensitivity shows higher average volatility than Medium and Low (observed)."
                    if high_is_higher
                    else "High sensitivity is not higher than both Medium and Low on average (observed)."
                )
            else:
                compare_note = "Insufficient data to compare High, Medium, and Low sensitivity."
    else:
        vol_summary = "N/A"
        compare_note = "Insufficient volatility data to compare sensitivity groups."

    insight_lines = [
        (
            f"Highest average volatility: **{top_vol['sector_label']}** ({top_vol['avg_volatility']:.2f})."
            if top_vol is not None
            else "Highest average volatility: **N/A**."
        ),
        (
            f"Lowest average return: **{low_ret['sector_label']}** ({low_ret['avg_return']:.2f}%)."
            if low_ret is not None
            else "Lowest average return: **N/A**."
        ),
        f"Average volatility by sensitivity: **{vol_summary}**.",
        compare_note,
    ]
    st.info("**Summary insights**\n" + "\n".join(f"- {line}" for line in insight_lines))

    st.plotly_chart(make_sector_performance_chart(filtered))
    st.caption("Indexed performance lines compare relative sector moves over time; patterns are associations, not causal.")

    st.plotly_chart(make_sector_average_return_bar(filtered))
    st.caption("Average daily return highlights sectors associated with stronger or weaker performance in the selected window.")

    st.plotly_chart(make_sector_volatility_boxplot(filtered))
    st.caption("Volatility distributions show how sensitivity groups are associated with different levels of variability.")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(make_sector_sensitivity_breakdown(filtered))
        st.caption("Counts show the composition of sector-country pairs by tariff sensitivity in the filtered data.")
    with right:
        st.plotly_chart(make_sector_return_volatility_scatter(filtered))
        st.caption("Each point is a day; return-versus-volatility relationships are observed, not causal.")

    st.markdown(
        f"""
        <div class="source-note">
            Source: <code>{SECTOR_PATH}</code>. Sector data covers USA, China, and global ETFs.
        </div>
        """,
        unsafe_allow_html=True,
    )
