from __future__ import annotations

from html import escape
import plotly.graph_objects as go

from core import *


def _compact_figure(fig: go.Figure, height: int = 220) -> go.Figure:
    fig.update_layout(
        showlegend=False,
        margin=dict(l=6, r=6, t=48),
        title=dict(font=dict(size=13)),
        hovermode="closest",
        height=height,
    )
    fig.update_xaxes(title_font=dict(size=10), tickfont=dict(size=10))
    fig.update_yaxes(title_font=dict(size=10), tickfont=dict(size=10))
    if hasattr(fig.layout, "coloraxis") and fig.layout.coloraxis:
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


def render_sector_impact_tab() -> None:
    df = load_sector_data(SECTOR_PATH)
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
        </style>
        <div class="page-title">
            <div class="impact-compact-title">
                <h1>Sectoral Impact</h1>
                <p>Identify sectors most affected by tariff uncertainty and observe how sensitivity relates to volatility.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    base = filter_by_date(df, "sector")
    c1, c2, c3 = st.columns(3)
    with c1:
        countries = sorted(base["country"].dropna().unique())
        selected_countries = _checkbox_dropdown("Countries", countries, countries, "sector_countries")
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
        selected_sectors = _checkbox_dropdown("Sectors", sectors, default_sectors, "sector_labels")
    with c3:
        sensitivities = sorted(base["tariff_sensitivity"].dropna().unique())
        selected_sensitivities = _checkbox_dropdown(
            "Tariff sensitivity",
            sensitivities,
            sensitivities,
            "sector_sensitivities",
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
        else:
            vol_by_sens["order"] = vol_by_sens["tariff_sensitivity"].map(
                {label: idx for idx, label in enumerate(sensitivity_order)}
            )
            vol_by_sens = vol_by_sens.sort_values("order")
            vol_summary = ", ".join(
                f"{row.tariff_sensitivity}: {row.avg_volatility:.2f}"
                for row in vol_by_sens.itertuples()
            )
    else:
        vol_summary = "N/A"

    top_vol_str = f"{top_vol['sector_label']} ({top_vol['avg_volatility']:.2f})" if top_vol is not None else "N/A"
    low_ret_str = f"{low_ret['sector_label']} ({low_ret['avg_return']:.2f}%)" if low_ret is not None else "N/A"
    trend_str = vol_summary

    st.markdown(
        f"""
        <div class="impact-kpis">
            <div class="impact-kpi"><span>Countries Selected</span><strong>{len(selected_countries)}</strong></div>
            <div class="impact-kpi"><span>Sectors Selected</span><strong>{len(selected_sectors)}</strong></div>
            <div class="impact-kpi"><span>Highest Volatility</span><strong>{escape(top_vol_str)}</strong></div>
            <div class="impact-kpi"><span>Lowest Return</span><strong>{escape(low_ret_str)}</strong></div>
            <div class="impact-kpi"><span>Avg Volatility by Sensitivity</span><strong>{escape(trend_str)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_left, top_mid, top_right = st.columns(3)
    with top_left:
        st.plotly_chart(
            _compact_figure(make_sector_performance_chart(filtered), height=compact_height),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with top_mid:
        st.plotly_chart(
            _compact_figure(make_sector_average_return_bar(filtered), height=compact_height),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with top_right:
        st.plotly_chart(
            _compact_figure(make_sector_volatility_boxplot(filtered), height=compact_height),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        st.plotly_chart(
            _compact_figure(make_sector_sensitivity_breakdown(filtered), height=compact_height),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with bottom_right:
        st.plotly_chart(
            _compact_figure(make_sector_return_volatility_scatter(filtered), height=compact_height),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with st.expander("Notes and source", expanded=False):
        st.caption(
            "Indexed performance lines compare relative sector moves over time; patterns are associations, not causal. "
            "Average daily return highlights sectors associated with stronger/weaker performance. "
            "Volatility distributions show sensitivity group variability. "
            f"Source: {SECTOR_PATH}. Sector data covers USA, China, and global ETFs."
        )

