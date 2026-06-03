from core import *

def filter_tariff_data(df: pd.DataFrame) -> pd.DataFrame:
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    c1, c2, c3, c4 = st.columns([1.2, 1.1, 1.1, 1.0])
    with c1:
        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="tariff_date_range",
        )
    with c2:
        type_options = sorted(df["type"].dropna().unique())
        selected_types = st.multiselect("Action type", type_options, default=type_options, key="tariff_types")
    with c3:
        imposing_options = sorted(df["imposing_label"].dropna().unique())
        selected_imposers = st.multiselect(
            "Imposing economy",
            imposing_options,
            default=imposing_options,
            key="tariff_imposers",
        )
    with c4:
        weight_mode = st.selectbox(
            "Network weight",
            ["Estimated trade value", "Event count"],
            index=0,
            key="tariff_weight_mode",
        )

    f1, f2, f3 = st.columns([1.1, 1.35, 0.9])
    with f1:
        target_options = sorted(df["target_label"].dropna().unique())
        selected_targets = st.multiselect(
            "Target economy",
            target_options,
            default=target_options,
            key="tariff_targets",
        )
    with f2:
        sector_options = sorted(df["sector"].dropna().unique())
        selected_sectors = st.multiselect("Sector", sector_options, default=sector_options, key="tariff_sectors")
    with f3:
        retaliation_filter = st.selectbox(
            "Retaliation",
            ["All", "Retaliation only", "Initial/policy only"],
            index=0,
            key="tariff_retaliation",
        )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start_date, end_date = pd.to_datetime(min_date), pd.to_datetime(max_date)

    filtered = df[
        (df["date"] >= start_date)
        & (df["date"] <= end_date)
        & (df["type"].isin(selected_types))
        & (df["imposing_label"].isin(selected_imposers))
        & (df["target_label"].isin(selected_targets))
        & (df["sector"].isin(selected_sectors))
    ].copy()
    if retaliation_filter == "Retaliation only":
        filtered = filtered[filtered["retaliation"]]
    elif retaliation_filter == "Initial/policy only":
        filtered = filtered[~filtered["retaliation"]]
    return filtered, weight_mode


def render_tariff_tensions_tab() -> None:
    df = load_tariff_data(TARIFF_PATH)
    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Global Tariff Tensions</h1>
                <p>Tariff events, retaliations, affected sectors, and directed pressure between economies.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    filtered, weight_mode = filter_tariff_data(df)
    if filtered.empty:
        st.warning("No tariff events match the current filters.")
        return

    event_count = len(filtered)
    known_value = filtered["known_trade_value"].sum()
    known_count = int(filtered["trade_value_known"].sum())
    avg_rate = filtered["tariff_rate_pct"].mean()
    retaliation_share = filtered["retaliation"].mean() * 100
    edges = aggregate_tariff_edges(filtered, weight_mode)
    top_edge = edges.iloc[0] if not edges.empty else None

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tariff events", f"{event_count:,}")
    k2.metric("Known affected trade", f"${known_value:,.1f}B", f"{known_count} events with value")
    k3.metric("Average tariff rate", f"{avg_rate:.1f}%")
    k4.metric("Retaliation share", f"{retaliation_share:.1f}%")

    if top_edge is not None:
        suffix = "USD bn" if weight_mode == "Estimated trade value" else "events"
        st.caption(
            f"Strongest visible edge by {weight_mode.lower()}: "
            f"{top_edge['imposing_label']} -> {top_edge['target_label']} "
            f"({top_edge['weight']:,.1f} {suffix})."
        )

    trend_col, year_col = st.columns(2)
    with trend_col:
        st.plotly_chart(make_tariff_cumulative_chart(filtered))
    with year_col:
        st.plotly_chart(make_tariff_actions_by_year(filtered))

    map_left, map_right = st.columns(2)
    with map_left:
        st.plotly_chart(make_tariff_country_map(filtered, "imposing", weight_mode))
    with map_right:
        st.plotly_chart(make_tariff_country_map(filtered, "target", weight_mode))

    st.plotly_chart(make_tariff_network(filtered, weight_mode))

    sector_col, tree_col = st.columns([1, 1])
    with sector_col:
        st.plotly_chart(make_tariff_sector_bar(filtered, weight_mode))
    with tree_col:
        st.plotly_chart(make_tariff_type_treemap(filtered))

    dist_col, scatter_col = st.columns(2)
    with dist_col:
        st.plotly_chart(make_tariff_rate_distribution(filtered))
    with scatter_col:
        st.plotly_chart(make_tariff_rate_value_scatter(filtered))

    source_col, notes_col = st.columns([0.92, 1.08])
    with source_col:
        st.plotly_chart(make_tariff_source_chart(filtered))
    with notes_col:
        st.subheader("Filtered tariff events")
        table = filtered[
            [
                "date",
                "imposing_label",
                "target_label",
                "sector",
                "tariff_rate_pct",
                "tariff_rate_delta",
                "estimated_trade_value_usd_bn",
                "type",
                "retaliation_label",
                "legal_basis",
                "source",
                "notes",
            ]
        ].sort_values("date", ascending=False)
        table = table.rename(
            columns={
                "date": "Date",
                "imposing_label": "Imposing",
                "target_label": "Target",
                "sector": "Sector",
                "tariff_rate_pct": "Rate %",
                "tariff_rate_delta": "Delta %",
                "estimated_trade_value_usd_bn": "Trade value USD bn",
                "type": "Type",
                "retaliation_label": "Retaliation",
                "legal_basis": "Legal basis",
                "source": "Source",
                "notes": "Notes",
            }
        )
        st.dataframe(
            table,
            width="stretch",
            hide_index=True,
            height=430,
            column_config={
                "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Rate %": st.column_config.NumberColumn("Rate %", format="%.1f"),
                "Delta %": st.column_config.NumberColumn("Delta %", format="%.1f"),
                "Trade value USD bn": st.column_config.NumberColumn("Trade value USD bn", format="%.1f"),
            },
        )

    st.markdown(
        f"""
        <div class="source-note">
            Source: <code>{TARIFF_PATH}</code>. Missing affected-trade values are included in event-count views but excluded from
            value-weighted maps, Sankey flows, and network weights.
        </div>
        """,
        unsafe_allow_html=True,
    )

