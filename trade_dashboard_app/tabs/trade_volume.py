from core import *

def render_trade_volume_tab() -> None:
    raw = load_trade_data(DATA_PATH)
    wide = prepare_trade_matrix(raw)
    years = sorted(wide["year"].dropna().unique().tolist())
    max_year = max(years)

    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Trade Volume Dashboard</h1>
                <p>Annual goods and services trade, adapted from the WTO merchandise dashboard layout.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns([1.25, 1.0, 0.85, 1.15])
    with c1:
        indicator = st.selectbox(
            "Indicator",
            ["Goods & services trade"],
            index=0,
        )
    with c2:
        trade_flow = st.selectbox(
            "Trade Flow",
            list(TRADE_FLOW_TO_LABEL.keys()),
            index=0,
        )
    with c3:
        year = st.selectbox("Year", years, index=years.index(max_year))
    with c4:
        country_options = sorted(wide["country"].unique())
        selected_country = st.selectbox(
            "Economy",
            country_options,
            index=country_options.index("China") if "China" in country_options else 0,
        )

    metric_col = TRADE_FLOW_TO_LABEL[trade_flow]
    year_df = selected_metric_frame(wide, year, metric_col)
    yoy = compute_yoy(wide, metric_col, year)
    year_df["yoy_change_pct"] = year_df["country"].map(yoy)

    total_value = year_df["metric_value"].sum()
    avg_yoy = year_df["yoy_change_pct"].mean()
    top_row = year_df.iloc[0] if not year_df.empty else None
    previous_total = selected_metric_frame(wide, year - 1, metric_col)["metric_value"].sum() if year - 1 in years else pd.NA
    if pd.isna(previous_total) or previous_total == 0:
        total_delta = pd.NA
    else:
        total_delta = (total_value - previous_total) / previous_total * 100

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Dataset total", format_usd(total_value), format_pct(total_delta))
    k2.metric("Average YoY change", format_pct(avg_yoy))
    if top_row is not None:
        k3.metric("Largest economy", top_row["country"], format_usd(top_row["metric_value"]))
    else:
        k3.metric("Largest economy", "n/a")
    k4.metric("Economies covered", f"{year_df['country'].nunique()} of {wide['country'].nunique()}")

    st.plotly_chart(make_map(year_df, trade_flow, year))

    left, right = st.columns([0.9, 1.45])
    with left:
        st.subheader(f"{trade_flow} by economy")
        table = year_df[
            ["rank", "country", "region", "metric_value", "yoy_change_pct", "dataset_share_pct", "period"]
        ].copy()
        table = table.rename(
            columns={
                "rank": "#",
                "country": "Economy",
                "region": "Region",
                "metric_value": "US$",
                "yoy_change_pct": "YoY %",
                "dataset_share_pct": "Share %",
                "period": "Period",
            }
        )
        st.dataframe(
            table,
            width="stretch",
            hide_index=True,
            column_config={
                "US$": st.column_config.NumberColumn("US$", format="$%.0f"),
                "YoY %": st.column_config.NumberColumn("YoY %", format="%.1f"),
                "Share %": st.column_config.NumberColumn("Share %", format="%.2f"),
            },
            height=430,
        )
    with right:
        st.plotly_chart(make_regional_bar(year_df, trade_flow))

    trend_left, trend_right = st.columns(2)
    with trend_left:
        st.plotly_chart(make_country_trend(wide, selected_country))
    with trend_right:
        st.plotly_chart(make_aggregate_trend(wide))

    st.plotly_chart(make_index_chart(wide, trade_flow, metric_col, min(years)))

    st.markdown(
        f"""
        <div class="source-note">
            Source: <code>{DATA_PATH}</code>. Values are annual and expressed in current US dollars.
            The file provides annual observations through {max_year}; monthly and quarterly panels from the original WTO
            merchandise dashboard are intentionally omitted in this first tab.
        </div>
        """,
        unsafe_allow_html=True,
    )


