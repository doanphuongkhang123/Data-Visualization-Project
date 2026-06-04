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
    with st.popover(f"{label} ({selected_count})", use_container_width=True):
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
            padding-top: 3rem !important;
        }
        .page-title {
            margin-top: -0.7rem;
            margin-bottom: 0.35rem;
            padding-bottom: 0.28rem;
        }
        .impact-compact-title h1 {
            font-size: 1.35rem;
            line-height: 1.2;
            margin: 0;
        }
        .impact-compact-title p {
            margin: 0;
            color: #667085;
            font-size: 0.82rem;
            line-height: 1.15;
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
            gap: 0.7rem;
            margin: 0.35rem 0 0.85rem;
        }
        .impact-kpi {
            border: 1px solid #d9dee7;
            border-top: 3px solid #20242a;
            color: #20242a;
            background: #f7f9fb;
            border-radius: 6px;
            padding: 0.8rem 0.65rem 0.7rem;
            min-width: 0;
            min-height: 92px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            text-align: center;
        }
        .impact-kpi:nth-child(2) { border-top-color: #0072B2; color: #0072B2; }
        .impact-kpi:nth-child(3) { border-top-color: #E69F00; color: #E69F00; }
        .impact-kpi:nth-child(4) { border-top-color: #D55E00; color: #D55E00; }
        .impact-kpi:nth-child(5) { border-top-color: #CC79A7; color: #CC79A7; }
        .impact-kpi span {
            display: block;
            color: #667085;
            font-size: 0.68rem;
            line-height: 1.1;
            margin-top: 0.35rem;
            text-transform: uppercase;
            letter-spacing: 0.45px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            order: 2;
        }
        .impact-kpi strong {
            display: block;
            color: inherit;
            font-size: 1.25rem;
            font-weight: 700;
            line-height: 1.15;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            order: 1;
        }
        .impact-kpi::after {
            content: "";
            width: 28px;
            height: 3px;
            border-radius: 2px;
            background: currentColor;
            margin: 0.45rem auto 0;
            order: 3;
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

    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    c_date, c1, c2, c3 = st.columns(
        [0.82, 1.12, 1.12, 1.12],
        vertical_alignment="bottom",
    )
    with c_date:
        selected_date = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="sector_date_range",
        )
        if isinstance(selected_date, tuple) and len(selected_date) == 2:
            start_date, end_date = pd.to_datetime(selected_date[0]), pd.to_datetime(selected_date[1])
        else:
            start_date, end_date = pd.to_datetime(min_date), pd.to_datetime(max_date)

    base = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()

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

    performance_height = 280
    secondary_height = performance_height

    top_left, top_right = st.columns([2, 1])
    with top_left:
        performance_fig = _compact_figure(make_sector_performance_chart(filtered), height=performance_height)
        performance_fig.update_layout(
            showlegend=True,
            legend=dict(
                title="Sector",
                orientation="h",
                y=-0.18,
                x=0,
                font=dict(size=9),
            ),
            margin=dict(l=6, r=6, t=48, b=58),
        )
        st.plotly_chart(
            performance_fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with top_right:
        st.plotly_chart(
            _compact_figure(make_sector_average_return_bar(filtered), height=performance_height),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    bottom_left, bottom_right = st.columns([2, 1])
    with bottom_left:
        st.plotly_chart(
            _compact_figure(make_sector_return_volatility_scatter(filtered), height=secondary_height),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with bottom_right:
        st.plotly_chart(
            _compact_figure(make_sector_volatility_boxplot(filtered), height=secondary_height),
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

