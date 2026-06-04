from core import *
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from html import escape

MARKET_COLORS = CVD_QUALITATIVE_COLORS
EVENT_COLORS = {"Near Tariff Event (+/-10d)": "#D55E00", "Normal Days": "#0072B2"}
PERFORMANCE_COLORS = {"Positive Return": "#0072B2", "Negative Return": "#D55E00"}

def reindex_to_100(df: pd.DataFrame) -> pd.DataFrame:
    """Dynamically reindexes stock close prices to 100 on the first date in the filtered dataset."""
    df = df.sort_values("date")
    reindexed_list = []
    for index_name, group in df.groupby("index_name"):
        group = group.copy()
        first_valid_close = group["close"].dropna().iloc[0] if not group["close"].dropna().empty else None
        if first_valid_close and first_valid_close != 0:
            group["indexed_to_100"] = (group["close"] / first_valid_close) * 100
        else:
            group["indexed_to_100"] = 100.0
        reindexed_list.append(group)
    return pd.concat(reindexed_list) if reindexed_list else df

def add_tariff_shading_rects(fig: go.Figure, df: pd.DataFrame) -> go.Figure:
    """Adds vertical shading bands to the chart for contiguous periods where tariff_event_nearby is True."""
    event_df = df[df["tariff_event_nearby"] == True].sort_values("date")
    if event_df.empty:
        return fig
    
    unique_dates = pd.to_datetime(event_df["date"].unique())
    if len(unique_dates) == 0:
        return fig
    
    # Group contiguous dates if they are within 4 days of each other
    event_ranges = []
    start = unique_dates[0]
    prev = unique_dates[0]
    for d in unique_dates[1:]:
        if (d - prev).days > 4:
            event_ranges.append((start, prev))
            start = d
        prev = d
    event_ranges.append((start, prev))
    
    # Shade each date range without adding static annotation text
    for s_dt, e_dt in event_ranges:
        fig.add_vrect(
            x0=s_dt,
            x1=e_dt,
            fillcolor="#D55E00",
            opacity=0.09,
            layer="below",
            line_width=0
        )
        
    fig.add_annotation(
        text="<span style='color:#D55E00'>Event window</span>",
        x=1.0, y=1.0,
        xanchor="right", yanchor="bottom",
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=10, color="#555"),
        bgcolor="rgba(255,255,255,0.0)"
    )
    return fig

def _compact_figure(fig: go.Figure, title_text: str = "") -> go.Figure:
    fig.update_layout(
        showlegend=False,
        margin=dict(l=6, r=6, t=32, b=24),
        title=dict(text=title_text, font=dict(size=13), x=0.02, y=0.96),
        hovermode="closest",
    )
    fig.update_xaxes(title_font=dict(size=10), tickfont=dict(size=10))
    fig.update_yaxes(title_font=dict(size=10), tickfont=dict(size=10))
    return fig

def _set_all_checkboxes(option_count: int, key_prefix: str) -> None:
    select_all = st.session_state.get(f"{key_prefix}_select_all", False)
    for idx in range(option_count):
        st.session_state[f"{key_prefix}_{idx}"] = select_all

def _sync_select_all(option_count: int, key_prefix: str) -> None:
    st.session_state[f"{key_prefix}_select_all"] = all(
        st.session_state.get(f"{key_prefix}_{idx}", False) for idx in range(option_count)
    )

def _selected_count(options: list[str], default: list[str], key_prefix: str) -> int:
    return sum(1 for idx, option in enumerate(options) if st.session_state.get(f"{key_prefix}_{idx}", option in default))

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

def _render_market_legends(indices: list[str], color_map: dict[str, str]) -> None:
    items = "\n".join(
        f"""<span class="market-legend-item">
    <span class="market-legend-swatch" style="background:{escape(color_map.get(idx, '#d1d5db'))};"></span>
    <span>{escape(idx)}</span>
</span>"""
        for idx in indices
    )
    st.markdown(
        f"""
<div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem;">
    <div class="market-legend">
        <span class="market-legend-title">Index colors</span>
        {items}
    </div>
    <div class="market-legend">
        <span class="market-legend-title">Proximity</span>
        <span class="market-legend-item"><span class="market-legend-swatch" style="background:#D55E00;"></span><span>Near Tariff Event (+/-10d)</span></span>
        <span class="market-legend-item"><span class="market-legend-swatch" style="background:#0072B2;"></span><span>Normal Days</span></span>
    </div>
    <div class="market-legend">
        <span class="market-legend-title">Performance</span>
        <span class="market-legend-item"><span class="market-legend-swatch" style="background:#0072B2;"></span><span>Positive Return</span></span>
        <span class="market-legend-item"><span class="market-legend-swatch" style="background:#D55E00;"></span><span>Negative Return</span></span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

def make_dynamic_performance_chart(df: pd.DataFrame, highlight_index: str = "None", show_shading: bool = True, height: int = 240) -> go.Figure:
    df = reindex_to_100(df)
    df["Event Status"] = df["tariff_event_nearby"].map({True: "Near Tariff Event (+/-10d)", False: "Normal Period"})
    
    unique_indices = df["index_name"].unique()
    if highlight_index != "None" and highlight_index in unique_indices:
        group = df[df["index_name"] == highlight_index].sort_values("date")
        latest_val = group["indexed_to_100"].iloc[-1] if not group.empty else 100.0
        highlight_color = PERFORMANCE_COLORS["Positive Return"] if latest_val >= 100.0 else PERFORMANCE_COLORS["Negative Return"]
        color_map = {idx: highlight_color if idx == highlight_index else "#d1d5db" for idx in unique_indices}
    else:
        color_map = {idx: MARKET_COLORS[i % len(MARKET_COLORS)] for i, idx in enumerate(sorted(unique_indices))}
        
    fig = px.line(
        df, x="date", y="indexed_to_100", color="index_name", color_discrete_map=color_map,
        labels={"date": "Date", "indexed_to_100": "Index Value", "index_name": "Index", "Event Status": "Event Status"},
        hover_data={"date": "|%Y-%m-%d", "indexed_to_100": ":.2f", "Event Status": True}
    )
    
    for trace in fig.data:
        if highlight_index != "None" and highlight_index in unique_indices:
            if trace.name == highlight_index:
                trace.line.width = 3.5
                trace.opacity = 1.0
            else:
                trace.line.width = 1.2
                trace.opacity = 0.35
        else:
            trace.line.width = 2.0
            trace.opacity = 0.85
            
    if show_shading:
        fig = add_tariff_shading_rects(fig, df)
    fig.add_hline(y=100, line_width=1, line_dash="dash", line_color="#667085")
    fig.update_layout(height=height, yaxis=dict(gridcolor="#e9edf3"), xaxis=dict(gridcolor="#e9edf3"), plot_bgcolor="white")
    return fig

def make_volatility_heatmap_chart(df: pd.DataFrame, highlight_index: str = "None", show_shading: bool = True, height: int = 240) -> go.Figure:
    df = df.copy()
    
    # Pivot to create a 2D matrix (x=date, y=index_name, z=volatility_20d)
    pivot_df = df.pivot(index='index_name', columns='date', values='volatility_20d')
    
    # If a specific index is highlighted, we can reorder the y-axis to put it at the top
    indices = list(pivot_df.index)
    if highlight_index != "None" and highlight_index in indices:
        indices.remove(highlight_index)
        indices.append(highlight_index)
        pivot_df = pivot_df.reindex(indices)
        
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        colorscale='Reds',
        colorbar=dict(title="Vol (%)", thickness=10, len=0.9, tickfont=dict(size=10)),
        hovertemplate='Date: %{x|%Y-%m-%d}<br>Index: %{y}<br>Volatility: %{z:.2f}%<extra></extra>'
    ))
            
    if show_shading:
        event_df = df[df["tariff_event_nearby"] == True].sort_values("date")
        if not event_df.empty:
            unique_dates = pd.to_datetime(event_df["date"].unique())
            if len(unique_dates) > 0:
                event_ranges = []
                start = prev = unique_dates[0]
                for d in unique_dates[1:]:
                    if (d - prev).days > 4:
                        event_ranges.append((start, prev))
                        start = d
                    prev = d
                event_ranges.append((start, prev))
                for s, e in event_ranges:
                    fig.add_shape(
                        type="rect",
                        x0=s, x1=e,
                        y0=1.01, y1=1.06,
                        xref="x", yref="paper",
                        fillcolor="#D55E00",
                        line_width=0,
                        layer="above"
                    )
            
            fig.add_annotation(
                text="<span style='color:#D55E00'>Event window</span>",
                x=1.0, y=1.07,
                xanchor="right", yanchor="bottom",
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=10, color="#555"),
                bgcolor="rgba(255,255,255,0.0)"
            )
        
    fig.update_layout(
        height=height, 
        yaxis=dict(title="Market index", tickfont=dict(size=10)), 
        xaxis=dict(title="Date", tickfont=dict(size=10), showgrid=False), 
        plot_bgcolor="white",
        margin=dict(l=0, r=0, t=32, b=0)
    )
    return fig

def make_avg_return_comparison_chart(df: pd.DataFrame, highlight_index: str = "None", height: int = 240) -> go.Figure:
    agg = df.groupby(["index_name", "tariff_event_nearby"], as_index=False)["daily_return_pct"].mean()
    agg["proximity_label"] = agg["tariff_event_nearby"].map({True: "Near Tariff Event (+/-10d)", False: "Normal Days"})
    active_highlight = highlight_index if highlight_index != "None" and highlight_index in set(agg["index_name"]) else "None"
    
    fig = px.bar(
        agg, x="index_name", y="daily_return_pct", color="proximity_label", barmode="group",
        labels={"index_name": "Market index", "daily_return_pct": "Avg return (%)", "proximity_label": "Proximity"},
        color_discrete_map=EVENT_COLORS
    )
    fig.update_traces(
        marker_line=dict(width=0.6, color="#ffffff"),
        opacity=1.0,
    )
    for trace in fig.data:
        trace.marker.opacity = [
            1.0 if custom_index == active_highlight or active_highlight == "None" else 0.28
            for custom_index in agg.loc[agg["proximity_label"] == trace.name, "index_name"]
        ]
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="#667085")
    fig.update_layout(height=height, yaxis=dict(gridcolor="#e9edf3", tickformat="+.3f" if agg["daily_return_pct"].abs().max() < 0.1 else "+.2f", rangemode="tozero"), xaxis=dict(tickangle=-30, gridcolor="#e9edf3"), plot_bgcolor="white")
    return fig

def make_top_indices_bar_chart(df: pd.DataFrame, highlight_index: str = "None", height: int = 240) -> go.Figure:
    returns = []
    for idx, group in df.groupby("index_name"):
        group = group.sort_values("date")
        if not group.empty:
            first_close = group["close"].dropna().iloc[0] if not group["close"].dropna().empty else None
            last_close = group["close"].dropna().iloc[-1] if not group["close"].dropna().empty else None
            if first_close and last_close and first_close != 0:
                tot_ret = ((last_close - first_close) / first_close) * 100
                returns.append({"index_name": idx, "total_return_pct": tot_ret})
                
    ret_df = pd.DataFrame(returns)
    if ret_df.empty:
        return go.Figure()
    
    ret_df = ret_df.sort_values("total_return_pct", ascending=True)
    ret_df["color_group"] = ret_df["total_return_pct"].apply(lambda val: "Positive Return" if val >= 0 else "Negative Return")
    
    fig = px.bar(
        ret_df, x="total_return_pct", y="index_name", color="color_group", orientation="h",
        labels={"total_return_pct": "Total return (%)", "index_name": "Market index", "color_group": "Performance"},
        color_discrete_map=PERFORMANCE_COLORS,
    )
    if highlight_index != "None" and highlight_index in set(ret_df["index_name"]):
        for trace in fig.data:
            trace.marker.opacity = [
                1.0 if index_name == highlight_index else 0.28
                for index_name in ret_df.loc[ret_df["color_group"] == trace.name, "index_name"]
            ]
            trace.marker.line = dict(width=0.8, color="#ffffff")
    fig.add_vline(x=0, line_width=1, line_dash="dash", line_color="#667085")
    max_abs_return = ret_df["total_return_pct"].abs().max()
    centered_range = [-max_abs_return * 1.12, max_abs_return * 1.12] if max_abs_return > 0 else [-1, 1]
    fig.update_layout(
        height=height,
        xaxis=dict(gridcolor="#e9edf3", tickformat="+.1f%", range=centered_range),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white",
    )
    return fig

def make_daily_return_boxplot(df: pd.DataFrame, group_by_col: str, highlight_index: str = "None", height: int = 240) -> go.Figure:
    df = df.copy()
    df["proximity_label"] = df["tariff_event_nearby"].map({True: "Near Tariff Event (+/-10d)", False: "Normal Days"})
    if group_by_col == "index_name" and highlight_index != "None" and highlight_index in set(df["index_name"]):
        df = df[df["index_name"] == highlight_index].copy()
    
    fig = px.box(
        df.dropna(subset=["daily_return_pct"]), x=group_by_col, y="daily_return_pct", color="proximity_label",
        labels={"daily_return_pct": "Daily return (%)", group_by_col: "Country" if group_by_col == "country" else "Market index", "proximity_label": "Proximity"},
        color_discrete_map=EVENT_COLORS,
        points=False
    )
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="#667085")
    fig.update_layout(height=height, yaxis=dict(gridcolor="#e9edf3"), xaxis=dict(tickangle=-30, gridcolor="#e9edf3"), plot_bgcolor="white")
    return fig

def render_financial_market_tab() -> None:
    df = load_stock_data(STOCK_PATH)
    df["tariff_event_nearby"] = df["tariff_event_nearby"].map({True: True, False: False, 'True': True, 'False': False, 1: True, 0: False})
    
    compact_height = 240

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
        .market-compact-title h1 {
            font-size: 1.35rem;
            line-height: 1.2;
            margin: 0;
        }
        .market-compact-title p {
            margin: 0;
            color: #667085;
            font-size: 0.82rem;
            line-height: 1.15;
        }
        .market-kpis {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.7rem;
            margin: 0.35rem 0 0.85rem;
        }
        .market-kpi {
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
        .market-kpi:nth-child(2) { border-top-color: #0072B2; color: #0072B2; }
        .market-kpi:nth-child(3) { border-top-color: #D55E00; color: #D55E00; }
        .market-kpi:nth-child(4) { border-top-color: #009E73; color: #009E73; }
        .market-kpi span {
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
        .market-kpi strong {
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
        .market-kpi::after {
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
        .market-legend {
            display: flex;
            align-items: center;
            gap: 0.45rem 0.75rem;
            flex-wrap: wrap;
            border: 1px solid #e5e9f0;
            border-radius: 6px;
            background: #ffffff;
            padding: 0.34rem 0.55rem;
            margin: -0.05rem 0 0.1rem;
            min-height: 1.85rem;
        }
        .market-legend-title {
            color: #667085;
            font-size: 0.72rem;
            font-weight: 600;
            margin-right: 0.2rem;
        }
        .market-legend-item {
            display: inline-flex;
            align-items: center;
            gap: 0.28rem;
            color: #20242a;
            font-size: 0.72rem;
            line-height: 1;
            white-space: nowrap;
        }
        .market-legend-swatch {
            width: 0.62rem;
            height: 0.62rem;
            border-radius: 50%;
            border: 1px solid rgba(32,36,42,0.18);
            flex: 0 0 auto;
        }
        </style>
        <div class="page-title">
            <div class="market-compact-title">
                <h1>Financial Market Reaction</h1>
                <p>Stock-index performance, volatility, and tariff-event proximity across major markets.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    
    c1, c2, c3, c4, c5 = st.columns([1.1, 1.0, 1.0, 1.0, 0.9], vertical_alignment="bottom")
    
    with c1:
        selected_date = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="market_custom_date_range",
        )
        if isinstance(selected_date, tuple) and len(selected_date) == 2:
            start_date, end_date = pd.to_datetime(selected_date[0]), pd.to_datetime(selected_date[1])
        else:
            start_date, end_date = pd.to_datetime(min_date), pd.to_datetime(max_date)

    base = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()
    countries = sorted(base["country"].dropna().unique())
    default_countries = [c for c in ["USA", "China", "Vietnam"] if c in countries]
    if not default_countries:
        default_countries = countries[:3]
        
    with c2:
        selected_countries = _checkbox_dropdown("Countries", countries, default_countries, "market_countries")
        
    available_indices = sorted(base[base["country"].isin(selected_countries)]["index_name"].dropna().unique())
    
    with c3:
        selected_indices = _checkbox_dropdown("Market indices", available_indices, available_indices, "market_indices")
        
    with c4:
        highlight_index = st.selectbox(
            "Highlight focus",
            options=["None"] + available_indices,
            index=0,
            key="market_highlight_index"
        )
        
    with c5:
        group_by = st.selectbox("Group boxplot", ["Country", "Index Name"], key="market_boxplot_groupby")
        group_col = "country" if group_by == "Country" else "index_name"

    filtered_all_days = base[base["country"].isin(selected_countries) & base["index_name"].isin(selected_indices)].copy()
    if filtered_all_days.empty:
        st.warning("No market data match the country and index filters.")
        return

    filtered = filtered_all_days.copy()

    # Layout Top Row: 3 Charts
    top_left, top_mid, top_right = st.columns(3)
    with top_left:
        performance_fig = _compact_figure(
            make_dynamic_performance_chart(filtered, highlight_index=highlight_index, show_shading=True, height=compact_height),
            "Index Performance (Base=100)"
        )
        performance_fig.update_layout(
            showlegend=True,
            legend=dict(
                title="Index",
                orientation="h",
                y=-0.26,
                x=0,
                font=dict(size=9),
            ),
            margin=dict(l=6, r=6, t=32, b=64),
        )
        st.plotly_chart(
            performance_fig,
            use_container_width=True, config={"displayModeBar": False}
        )
    with top_mid:
        st.plotly_chart(
            _compact_figure(
                make_volatility_heatmap_chart(filtered, highlight_index=highlight_index, show_shading=True, height=compact_height),
                "20-Day Rolling Volatility"
            ),
            use_container_width=True, config={"displayModeBar": False}
        )
    with top_right:
        avg_return_fig = _compact_figure(
            make_avg_return_comparison_chart(filtered_all_days, highlight_index=highlight_index, height=compact_height),
            "Avg Daily Return (Event vs Normal)"
        )
        avg_return_fig.update_layout(
            showlegend=True,
            legend=dict(
                title="Proximity",
                orientation="h",
                y=-0.26,
                x=0,
                font=dict(size=9),
            ),
            margin=dict(l=6, r=6, t=32, b=64),
        )
        st.plotly_chart(
            avg_return_fig,
            use_container_width=True, config={"displayModeBar": False}
        )

    # Layout Bottom Row: 2 Charts
    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        st.plotly_chart(
            _compact_figure(
                make_top_indices_bar_chart(filtered_all_days, highlight_index=highlight_index, height=compact_height),
                "Total Return by Index"
            ),
            use_container_width=True, config={"displayModeBar": False}
        )
    with bottom_right:
        box_highlight = highlight_index if group_col == "index_name" else "None"
        st.plotly_chart(
            _compact_figure(
                make_daily_return_boxplot(filtered_all_days, group_col, highlight_index=box_highlight, height=compact_height),
                f"Daily Return Dist ({group_by})"
            ),
            use_container_width=True, config={"displayModeBar": False}
        )

    st.caption(f"Source: {{STOCK_PATH}}. Dynamically reindexed to 100 on the starting date of the selected window for accurate line chart comparison.")
