from core import *
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Custom premium color palette matching the WTO theme
MARKET_COLORS = ["#227c74", "#4C78A8", "#b15c63", "#D9895B", "#7b61a8", "#8a8f36", "#5B8C7A"]

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
            fillcolor="#d9895b",
            opacity=0.09,
            layer="below",
            line_width=0
        )
    return fig

def make_dynamic_performance_chart(df: pd.DataFrame, highlight_index: str = "None", show_shading: bool = True) -> go.Figure:
    """Generates the Line Chart for stock performance indexed to 100 at the start of the window."""
    df = reindex_to_100(df)
    # Add a formatted column for the hover tooltip
    df["Event Status"] = df["tariff_event_nearby"].map({True: "Near Tariff Event (±10d)", False: "Normal Period"})
    
    unique_indices = df["index_name"].unique()
    if highlight_index != "None" and highlight_index in unique_indices:
        # Highlight index color based on return: positive is teal, negative is red/coral
        group = df[df["index_name"] == highlight_index].sort_values("date")
        latest_val = group["indexed_to_100"].iloc[-1] if not group.empty else 100.0
        highlight_color = "#227c74" if latest_val >= 100.0 else "#b15c63"
        color_map = {idx: highlight_color if idx == highlight_index else "#d1d5db" for idx in unique_indices}
    else:
        # Standard colors
        color_map = {idx: MARKET_COLORS[i % len(MARKET_COLORS)] for i, idx in enumerate(sorted(unique_indices))}
        
    fig = px.line(
        df,
        x="date",
        y="indexed_to_100",
        color="index_name",
        color_discrete_map=color_map,
        title=None, # Removed to prevent collision with top legend
        labels={"date": "Date", "indexed_to_100": "Index Value", "index_name": "Index", "Event Status": "Event Status"},
        hover_data={"date": "|%Y-%m-%d", "indexed_to_100": ":.2f", "Event Status": True}
    )
    
    # Adjust line widths and opacity to highlight the chosen index and dim the others
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
            trace.opacity = 0.95
            
    if show_shading:
        fig = add_tariff_shading_rects(fig, df)
    fig.update_layout(
        height=450, # Slightly reduced height for better vertical harmony
        legend=dict(orientation="h", y=1.05, x=0, yanchor="bottom", xanchor="left", title=None),
        yaxis=dict(gridcolor="#e9edf3", ticksuffix="%"),
        xaxis=dict(gridcolor="#e9edf3"),
        margin=dict(b=40, t=20),
        plot_bgcolor="white",
        hovermode="x unified"
    )
    return fig

def make_volatility_line_chart(df: pd.DataFrame, highlight_index: str = "None", show_shading: bool = True) -> go.Figure:
    """Generates a Line Chart of the 20-day volatility over time."""
    df = df.copy()
    # Add a formatted column for the hover tooltip
    df["Event Status"] = df["tariff_event_nearby"].map({True: "Near Tariff Event (±10d)", False: "Normal Period"})
    
    unique_indices = df["index_name"].unique()
    if highlight_index != "None" and highlight_index in unique_indices:
        # Standard highlight color for volatility
        color_map = {idx: "#D9895B" if idx == highlight_index else "#d1d5db" for idx in unique_indices}
    else:
        color_map = {idx: MARKET_COLORS[i % len(MARKET_COLORS)] for i, idx in enumerate(sorted(unique_indices))}
        
    fig = px.line(
        df,
        x="date",
        y="volatility_20d",
        color="index_name",
        color_discrete_map=color_map,
        title=None, # Removed to prevent collision with top legend
        labels={"date": "Date", "volatility_20d": "20d Volatility (%)", "index_name": "Index", "Event Status": "Event Status"},
        hover_data={"date": "|%Y-%m-%d", "volatility_20d": ":.3f", "Event Status": True}
    )
    
    # Adjust line widths and opacity based on highlight
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
            trace.opacity = 0.95
            
    if show_shading:
        fig = add_tariff_shading_rects(fig, df)
    fig.update_layout(
        height=420, # Reduced height
        legend=dict(orientation="h", y=1.05, x=0, yanchor="bottom", xanchor="left", title=None),
        yaxis=dict(gridcolor="#e9edf3", ticksuffix="%"),
        xaxis=dict(gridcolor="#e9edf3"),
        margin=dict(b=40, t=20),
        plot_bgcolor="white",
        hovermode="x unified"
    )
    return fig

def make_avg_return_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """Generates a Grouped Bar Chart comparing average daily return on event days vs normal days."""
    agg = df.groupby(["index_name", "tariff_event_nearby"], as_index=False)["daily_return_pct"].mean()
    agg["proximity_label"] = agg["tariff_event_nearby"].map({True: "Near Tariff Event (±10d)", False: "Normal Days"})
    
    fig = px.bar(
        agg,
        x="index_name",
        y="daily_return_pct",
        color="proximity_label",
        barmode="group",
        title=None, # Removed to prevent collision
        labels={"index_name": "", "daily_return_pct": "Avg Return (%)", "proximity_label": "Proximity"},
        color_discrete_map={
            "Near Tariff Event (±10d)": "#b15c63",
            "Normal Days": "#5B8C7A"
        }
    )
    fig.update_layout(
        height=420, # Reduced height to match volatility chart
        legend=dict(orientation="h", y=1.05, x=0, yanchor="bottom", xanchor="left", title=None),
        yaxis=dict(gridcolor="#e9edf3", tickformat="+.3f" if agg["daily_return_pct"].abs().max() < 0.1 else "+.2f"),
        xaxis=dict(tickangle=-30, gridcolor="#e9edf3"),
        margin=dict(b=130, t=20), # Large margin for rotated labels
        plot_bgcolor="white"
    )
    return fig

def make_top_indices_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Generates a Horizontal Bar Chart comparing total period return for each index."""
    returns = []
    for idx, group in df.groupby("index_name"):
        group = group.sort_values("date")
        if not group.empty:
            first_close = group["close"].dropna().iloc[0] if not group["close"].dropna().empty else None
            last_close = group["close"].dropna().iloc[-1] if not group["close"].dropna().empty else None
            country = group["country"].iloc[0]
            if first_close and last_close and first_close != 0:
                tot_ret = ((last_close - first_close) / first_close) * 100
                returns.append({"index_name": idx, "country": country, "total_return_pct": tot_ret})
                
    ret_df = pd.DataFrame(returns)
    if ret_df.empty:
        return go.Figure()
    
    ret_df = ret_df.sort_values("total_return_pct", ascending=True)
    ret_df["color_group"] = ret_df["total_return_pct"].apply(lambda val: "Positive Return" if val >= 0 else "Negative Return")
    
    fig = px.bar(
        ret_df,
        x="total_return_pct",
        y="index_name",
        color="color_group",
        orientation="h",
        title=None, # Removed to prevent collision
        labels={"total_return_pct": "Total Return (%)", "index_name": "", "color_group": "Performance"},
        color_discrete_map={
            "Positive Return": "#227c74",
            "Negative Return": "#b15c63"
        }
    )
    fig.update_layout(
        height=420, # Reduced height
        legend=dict(orientation="h", y=1.05, x=0, yanchor="bottom", xanchor="left", title=None),
        xaxis=dict(gridcolor="#e9edf3", tickformat="+.1f%"),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=150, b=40, t=20), # Expand left margin to fit long index names
        plot_bgcolor="white"
    )
    return fig

def make_daily_return_boxplot(df: pd.DataFrame, group_by_col: str) -> go.Figure:
    """Generates a Box Plot comparing daily return distributions on event vs normal days."""
    df = df.copy()
    df["proximity_label"] = df["tariff_event_nearby"].map({True: "Near Tariff Event (±10d)", False: "Normal Days"})
    
    fig = px.box(
        df.dropna(subset=["daily_return_pct"]),
        x=group_by_col,
        y="daily_return_pct",
        color="proximity_label",
        title=None, # Removed to prevent collision
        labels={"daily_return_pct": "Daily Return (%)", group_by_col: "", "proximity_label": "Proximity"},
        color_discrete_map={
            "Near Tariff Event (±10d)": "#b15c63",
            "Normal Days": "#4C78A8"
        }
    )
    fig.update_layout(
        height=420, # Reduced height
        legend=dict(orientation="h", y=1.05, x=0, yanchor="bottom", xanchor="left", title=None),
        yaxis=dict(gridcolor="#e9edf3"),
        xaxis=dict(tickangle=-30, gridcolor="#e9edf3"),
        margin=dict(b=130, t=20), # Large margin for rotated labels
        plot_bgcolor="white"
    )
    return fig

def render_financial_market_tab() -> None:
    df = load_stock_data(STOCK_PATH)
    # Ensure proximity column is treated as boolean
    df["tariff_event_nearby"] = df["tariff_event_nearby"].map({True: True, False: False, 'True': True, 'False': False, 1: True, 0: False})
    
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

    # Render Filter Panel inside a beautiful Card wrapper
    with st.container(border=True):
        min_date = df["date"].min().date()
        max_date = df["date"].max().date()
        
        f1, f2, f3, f4 = st.columns([0.9, 1.1, 1.25, 0.75])
        
        with f1:
            selected_date = st.date_input(
                "Date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="market_custom_date_range",
            )
            # Parse custom date range safely
            if isinstance(selected_date, tuple) and len(selected_date) == 2:
                start_date, end_date = pd.to_datetime(selected_date[0]), pd.to_datetime(selected_date[1])
            else:
                start_date, end_date = pd.to_datetime(min_date), pd.to_datetime(max_date)

        # Base filtered by date
        base = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()
        
        with f2:
            countries = sorted(base["country"].dropna().unique())
            # Default to curated set (USA, China, Vietnam) if present, otherwise select the first 3
            default_countries = [c for c in ["USA", "China", "Vietnam"] if c in countries]
            if not default_countries:
                default_countries = countries[:3]
            selected_countries = st.multiselect("Countries", countries, default=default_countries, key="market_countries")
            
        with f3:
            available_indices = sorted(base[base["country"].isin(selected_countries)]["index_name"].dropna().unique())
            # Default to all indices corresponding to selected countries
            selected_indices = st.multiselect("Market indices", available_indices, default=available_indices, key="market_indices")
            
        with f4:
            proximity_filter = st.selectbox(
                "Tariff Proximity",
                ["All Days", "Near Tariff Events (±10d) Only", "Normal Days Only"],
                key="market_tariff_proximity"
            )

    # Build base filtered dataframe without the proximity subsetting for metric and comparison cards
    filtered_all_days = base[base["country"].isin(selected_countries) & base["index_name"].isin(selected_indices)].copy()
    if filtered_all_days.empty:
        st.warning("No market data match the country and index filters.")
        return

    # Metrics Section
    latest = make_latest_table(filtered_all_days, ["country", "index_name"])
    leader = latest.sort_values("indexed_to_100", ascending=False).iloc[0] if not latest.empty else None
    laggard = latest.sort_values("indexed_to_100", ascending=True).iloc[0] if not latest.empty else None
    event_avg = filtered_all_days.loc[filtered_all_days["tariff_event_nearby"] == True, "daily_return_pct"].mean()
    normal_avg = filtered_all_days.loc[filtered_all_days["tariff_event_nearby"] == False, "daily_return_pct"].mean()
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Markets covered", f"{filtered_all_days['index_name'].nunique()}")
    
    if leader is not None:
        k2.metric("Best latest index", leader["index_name"], f"{leader['indexed_to_100']:.1f}")
    else:
        k2.metric("Best latest index", "n/a")
        
    if laggard is not None:
        k3.metric("Weakest latest index", laggard["index_name"], f"{laggard['indexed_to_100']:.1f}")
    else:
        k3.metric("Weakest latest index", "n/a")
        
    k4.metric("Avg Event Return vs Normal", format_pct(event_avg), f"Normal: {format_pct(normal_avg)}")

    # Subset the active dataframe for the time series charts based on the proximity filter
    filtered = filtered_all_days.copy()
    if proximity_filter == "Near Tariff Events (±10d) Only":
        filtered = filtered[filtered["tariff_event_nearby"] == True]
    elif proximity_filter == "Normal Days Only":
        filtered = filtered[filtered["tariff_event_nearby"] == False]

    if filtered.empty:
        st.warning("No data match the selected filters, including the proximity subsetting.")
        return

    # Render Trends Row
    st.markdown("### Market Performance and Volatility Trends")
    
    # Highlight focus index selector to solve the spaghetti line chart issue
    indices_in_filtered = sorted(filtered["index_name"].unique())
    hl_col, _ = st.columns([1.5, 2.5])
    with hl_col:
        highlight_index = st.selectbox(
            "Highlight focus index (dims all other lines to gray)",
            options=["None"] + indices_in_filtered,
            index=0,
            key="market_highlight_index"
        )
        
    st.markdown("#### Stock Index Performance (Dynamic Base = 100)")
    st.plotly_chart(make_dynamic_performance_chart(filtered, highlight_index=highlight_index, show_shading=(proximity_filter == "All Days")), use_container_width=True)
    
    left, right = st.columns(2)
    with left:
        st.markdown("#### 20-Day Rolling Volatility Trend")
        st.plotly_chart(make_volatility_line_chart(filtered, highlight_index=highlight_index, show_shading=(proximity_filter == "All Days")), use_container_width=True)
    with right:
        st.markdown("#### Average Daily Return: Near Tariff Events vs. Normal Days")
        st.plotly_chart(make_avg_return_comparison_chart(filtered_all_days), use_container_width=True)
        
    # Render Distributions Row
    st.markdown("### Return Performance and Distribution Analysis")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Total Percentage Return by Index (Period Overall)")
        st.plotly_chart(make_top_indices_bar_chart(filtered_all_days), use_container_width=True)
    with right:
        # Toggle option to change boxplot grouping
        group_by = st.radio("Group Boxplot By", ["Country", "Index Name"], horizontal=True, key="market_boxplot_groupby")
        group_col = "country" if group_by == "Country" else "index_name"
        st.markdown(f"#### Daily Return Distribution Grouped by {group_by}")
        st.plotly_chart(make_daily_return_boxplot(filtered_all_days, group_col), use_container_width=True)

    st.markdown(
        f"""
        <div class="source-note">
            Source: <code>{STOCK_PATH}</code>. Dynamically reindexed to 100 on the starting date of the selected window for accurate line chart comparison.
        </div>
        """,
        unsafe_allow_html=True,
    )
