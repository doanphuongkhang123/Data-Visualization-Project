from __future__ import annotations

from core import *


# ── Colour palette ──────────────────────────────────────────────────────
ACCENT_TEAL = "#227c74"
ACCENT_CORAL = "#b15c63"
ACCENT_GOLD = "#d9895b"
ACCENT_BLUE = "#4c78a8"
ACCENT_PURPLE = "#7b61a8"

KPI_PALETTE = [ACCENT_TEAL, ACCENT_BLUE, ACCENT_GOLD, ACCENT_CORAL, ACCENT_PURPLE]
BAR_COLOR_SCALE = [
    [0, "#e0f0ee"],
    [0.35, "#88c4bc"],
    [0.65, "#3a9e91"],
    [1, ACCENT_TEAL],
]

TYPE_ACCENT = {
    "New Tariff": ACCENT_TEAL,
    "Escalation": ACCENT_CORAL,
    "Retaliation": ACCENT_GOLD,
    "Reduction": ACCENT_BLUE,
    "Universal Baseline": ACCENT_PURPLE,
    "Expansion": "#8a8f36",
    "Export Restriction": "#6b7a8f",
}

# ── Sector normalisation map ───────────────────────────────────────────
# Maps raw multi-category sector strings to a clean primary category.
_SECTOR_MAP = {
    "All Goods": "Broad / All Goods",
    "General": "Broad / All Goods",
    "Steel": "Steel & Metals",
    "Aluminum": "Steel & Metals",
    "Steel, Aluminum": "Steel & Metals",
    "Steel, Consumer, Agriculture": "Steel & Metals",
    "Steel, Aluminum, Consumer": "Steel & Metals",
    "Steel, Pork, Cheese, Apples": "Steel & Metals",
    "Steel, Bourbon, Motorcycles": "Steel & Metals",
    "Steel, Agriculture, Consumer": "Steel & Metals",
    "Consumer Goods, Steel": "Steel & Metals",
    "Consumer Goods, Furniture, Electronics": "Consumer Goods",
    "Consumer Electronics, Apparel, Footwear": "Consumer Goods",
    "Consumer Goods, Phase 1 Rollback": "Consumer Goods",
    "Airbus, Cheese, Wine": "Consumer Goods",
    "Agriculture, Autos, Seafood": "Agriculture & Food",
    "Agriculture, LNG, Chemicals": "Agriculture & Food",
    "Agriculture, Energy": "Agriculture & Food",
    "Agriculture": "Agriculture & Food",
    "Dairy, Pork": "Agriculture & Food",
    "LNG, Agriculture, Aircraft": "Agriculture & Food",
    "Coal, Oil, Medical, Autos": "Energy & Industrial",
    "Tech, Industrial, Aerospace": "Technology & Semiconductors",
    "Semiconductors, Chemicals, Rail": "Technology & Semiconductors",
    "Semiconductors, AI Chips": "Technology & Semiconductors",
    "Semiconductors": "Technology & Semiconductors",
    "Pharma, Electronics": "Technology & Semiconductors",
    "EVs": "Electric Vehicles",
    "Gallium, Germanium": "Critical Materials",
    "Graphite": "Critical Materials",
}


# ── Data cleaning helper ───────────────────────────────────────────────
def _clean_overview_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning rules specific to the Executive Overview page."""
    work = df.copy()

    # 1. Remove NewsAPI rows – they are news alerts, not official actions
    work = work[work["type"] != "NewsAPI"].copy()

    # 2. Standardize type: merge 'Export Control' into 'Export Restriction'
    work["type"] = work["type"].replace({"Export Control": "Export Restriction"})

    # 3. Standardize country codes using the normalize helper from core
    work["imposing_clean"] = work["imposing_country"].map(normalize_entity)
    work["target_clean"] = work["target_country"].map(normalize_entity)

    # 4. Derive year from date for time-aggregated views
    work["year"] = work["date"].dt.year

    # 5. Normalise sectors — merge redundant multi-category entries
    work["sector_clean"] = work["sector"].map(
        lambda s: _SECTOR_MAP.get(s, s)
    )

    return work


# ── KPI cards — self-contained HTML component ──────────────────────────
def _render_kpi_cards(kpis: list[tuple]) -> None:
    """Render all KPI cards as a single streamlit component with embedded
    CSS + JS so that styles and the count-up animation work reliably."""
    import streamlit.components.v1 as components

    # Build individual card divs
    card_divs = ""
    for label, target, prefix, suffix, decimals, accent in kpis:
        init = "0" if decimals == 0 else f"0.{'0' * decimals}"
        card_divs += f"""
        <div class="kpi-card" style="border-top: 3px solid {accent};">
            <div class="kpi-value" style="color: {accent};"
                 data-target="{target}" data-prefix="{prefix}"
                 data-suffix="{suffix}" data-decimals="{decimals}">
                {prefix}{init}{suffix}
            </div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-divider" style="background: {accent};"></div>
        </div>"""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: "Source Sans Pro", -apple-system, BlinkMacSystemFont,
                         "Segoe UI", Roboto, sans-serif;
            background: transparent;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 1rem;
            padding: 4px 0;
        }}
        .kpi-card {{
            background: #f7f9fb;
            border: 1px solid #d9dee7;
            border-radius: 10px;
            padding: 1.25rem 0.8rem 1.1rem;
            text-align: center;
            min-height: 108px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            transition: box-shadow 0.25s ease, transform 0.25s ease;
        }}
        .kpi-card:hover {{
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            transform: translateY(-2px);
        }}
        .kpi-value {{
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: -0.5px;
            line-height: 1.2;
            font-variant-numeric: tabular-nums;
        }}
        .kpi-label {{
            color: #667085;
            font-size: 0.72rem;
            margin-top: 0.45rem;
            text-transform: uppercase;
            letter-spacing: 0.7px;
            font-weight: 500;
        }}
        .kpi-divider {{
            width: 28px;
            height: 3px;
            border-radius: 2px;
            margin: 0.5rem auto 0;
        }}
    </style>
    </head>
    <body>
    <div class="kpi-grid">
        {card_divs}
    </div>
    <script>
    (function() {{
        document.querySelectorAll('.kpi-value[data-target]').forEach(function(el) {{
            var prefix = el.getAttribute('data-prefix') || '';
            var suffix = el.getAttribute('data-suffix') || '';
            var decimals = parseInt(el.getAttribute('data-decimals') || '0');
            var target = parseFloat(el.getAttribute('data-target'));
            var duration = 1400;
            var start = performance.now();
            function step(now) {{
                var elapsed = now - start;
                var progress = Math.min(elapsed / duration, 1);
                var ease = 1 - Math.pow(1 - progress, 3);
                var current = target * ease;
                if (decimals > 0) {{
                    el.textContent = prefix + current.toFixed(decimals) + suffix;
                }} else {{
                    el.textContent = prefix + Math.round(current).toLocaleString() + suffix;
                }}
                if (progress < 1) requestAnimationFrame(step);
            }}
            requestAnimationFrame(step);
        }});
    }})();
    </script>
    </body>
    </html>
    """
    components.html(html, height=135, scrolling=False)


# ── Chart A: Trend Over Time (dual-axis) ───────────────────────────────
def _chart_trend_over_time(df: pd.DataFrame) -> go.Figure:
    yearly = df.groupby("year", as_index=False).agg(
        event_count=("type", "size"),
        avg_rate=("tariff_rate_pct", "mean"),
    )

    fig = go.Figure()

    # Bar: event count
    fig.add_trace(
        go.Bar(
            x=yearly["year"],
            y=yearly["event_count"],
            name="Tariff Events",
            marker_color=ACCENT_TEAL,
            opacity=0.82,
            hovertemplate="<b>%{x}</b><br>Events: %{y}<extra></extra>",
            yaxis="y",
        )
    )

    # Line: average rate on secondary axis
    fig.add_trace(
        go.Scatter(
            x=yearly["year"],
            y=yearly["avg_rate"],
            name="Avg Tariff Rate (%)",
            mode="lines+markers",
            line=dict(color=ACCENT_CORAL, width=3),
            marker=dict(size=9, color=ACCENT_CORAL, line=dict(width=2, color="#fff")),
            hovertemplate="<b>%{x}</b><br>Avg Rate: %{y:.1f}%<extra></extra>",
            yaxis="y2",
        )
    )

    fig.update_layout(
        title=dict(text="Tariff Activity & Average Rate by Year", font=dict(size=17)),
        height=420,
        margin=dict(l=0, r=10, t=56, b=0),
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
        xaxis=dict(title="", dtick=1, gridcolor="#eef1f6"),
        yaxis=dict(
            title=dict(text="Number of Events", font=dict(color=ACCENT_TEAL)),
            tickfont=dict(color=ACCENT_TEAL),
            gridcolor="#eef1f6",
        ),
        yaxis2=dict(
            title=dict(text="Average Tariff Rate (%)", font=dict(color=ACCENT_CORAL)),
            tickfont=dict(color=ACCENT_CORAL),
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        plot_bgcolor="#ffffff",
        bargap=0.35,
    )
    return fig


# ── Chart B: Top Target Countries ──────────────────────────────────────
def _chart_top_targets(df: pd.DataFrame) -> go.Figure:
    target_counts = (
        df.groupby("target_clean", as_index=False)
        .size()
        .rename(columns={"size": "events"})
        .sort_values("events", ascending=True)
        .tail(10)
    )
    # Replace codes with readable labels
    target_counts["label"] = target_counts["target_clean"].map(entity_label)

    fig = px.bar(
        target_counts,
        x="events",
        y="label",
        orientation="h",
        color="events",
        color_continuous_scale=BAR_COLOR_SCALE,
        labels={"events": "Number of Tariff Actions", "label": ""},
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Events: %{x}<extra></extra>",
        texttemplate="%{x}",
        textposition="outside",
        textfont=dict(size=12, color="#444"),
    )
    fig.update_layout(
        title=dict(text="Most Frequently Targeted Countries", font=dict(size=17)),
        height=420,
        margin=dict(l=0, r=40, t=56, b=0),
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
        xaxis=dict(gridcolor="#eef1f6", title=""),
        plot_bgcolor="#ffffff",
    )
    # Reverse so largest on top
    fig.update_yaxes(autorange=True)
    return fig


# ── Chart C: Top Affected Sectors (cleaned) ────────────────────────────
def _chart_top_sectors(df: pd.DataFrame) -> go.Figure:
    sector_counts = (
        df.groupby("sector_clean", as_index=False)
        .size()
        .rename(columns={"size": "events"})
        .sort_values("events", ascending=True)
        .tail(10)
    )

    fig = px.bar(
        sector_counts,
        x="events",
        y="sector_clean",
        orientation="h",
        color="events",
        color_continuous_scale=[
            [0, "#fce8de"],
            [0.35, "#e8a988"],
            [0.65, "#d17e55"],
            [1, ACCENT_GOLD],
        ],
        labels={"events": "Number of Tariff Actions", "sector_clean": ""},
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Events: %{x}<extra></extra>",
        texttemplate="%{x}",
        textposition="outside",
        textfont=dict(size=12, color="#444"),
    )
    fig.update_layout(
        title=dict(text="Top Affected Sectors", font=dict(size=17)),
        height=420,
        margin=dict(l=0, r=40, t=56, b=0),
        coloraxis_showscale=False,
        yaxis=dict(tickfont=dict(size=11)),
        xaxis=dict(gridcolor="#eef1f6", title=""),
        plot_bgcolor="#ffffff",
    )
    fig.update_yaxes(autorange=True)
    return fig

# ── Chart D: Action Type Breakdown (donut) ─────────────────────────────
def _chart_action_type_breakdown(df: pd.DataFrame) -> go.Figure:
    """Donut chart showing distribution of trade actions by type."""
    type_counts = (
        df.groupby("type", as_index=False)
        .agg(
            events=("type", "size"),
            total_value=("estimated_trade_value_usd_bn", "sum"),
        )
        .sort_values("events", ascending=False)
    )

    colors = [TYPE_ACCENT.get(t, "#8d99ae") for t in type_counts["type"]]

    # Hover: show count + total trade value
    hover_texts = []
    for _, row in type_counts.iterrows():
        val = row["total_value"]
        val_str = f"${val/1000:.1f}T" if val >= 1000 else f"${val:.0f}B"
        hover_texts.append(
            f"<b>{row['type']}</b><br>"
            f"Events: {row['events']}<br>"
            f"Trade Value: {val_str}"
        )

    fig = go.Figure(
        go.Pie(
            labels=type_counts["type"],
            values=type_counts["events"],
            hole=0.52,
            marker=dict(
                colors=colors,
                line=dict(color="#ffffff", width=2),
            ),
            textinfo="label+percent",
            textposition="outside",
            textfont=dict(size=11),
            hovertext=hover_texts,
            hoverinfo="text",
            pull=[0.03 if i == 0 else 0 for i in range(len(type_counts))],
        )
    )

    fig.update_layout(
        title=dict(text="Action Type Distribution", font=dict(size=17)),
        height=420,
        margin=dict(l=10, r=10, t=56, b=10),
        showlegend=False,
        plot_bgcolor="#ffffff",
        annotations=[
            dict(
                text=f"<b>{len(df)}</b><br><span style='font-size:11px;color:#667085'>events</span>",
                x=0.5, y=0.5,
                font=dict(size=22, color="#20242a"),
                showarrow=False,
            )
        ],
    )
    return fig


# ── Main render function ───────────────────────────────────────────────
def render_executive_overview_tab() -> None:
    raw = load_tariff_data(TARIFF_PATH)
    df = _clean_overview_data(raw)

    # ── Page header ─────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Executive Overview</h1>
                <p>High-level narrative of the global trade war — policy actions, affected economies, and key milestones.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.warning("No official tariff events found after filtering out news alerts.")
        return

    # ── Compute KPI metrics ─────────────────────────────────────────────
    total_events = len(df)
    avg_rate = df["tariff_rate_pct"].mean()
    total_trade_value = df["estimated_trade_value_usd_bn"].sum()

    all_countries = set(df["imposing_clean"].dropna().unique()) | set(
        df["target_clean"].dropna().unique()
    )
    countries_involved = len(all_countries)
    sectors_affected = df["sector_clean"].nunique()

    if total_trade_value >= 1000:
        tv_target = total_trade_value / 1000
        tv_prefix, tv_suffix, tv_dec = "$", " Trillion", 1
    else:
        tv_target = total_trade_value
        tv_prefix, tv_suffix, tv_dec = "$", " Billion", 1

    # ── KPI Cards (Row 1) ──────────────────────────────────────────────
    kpis = [
        ("Total Tariff Events", total_events, "", "", 0, KPI_PALETTE[0]),
        ("Average Tariff Rate", avg_rate, "", "%", 1, KPI_PALETTE[1]),
        ("Trade Value Affected", tv_target, tv_prefix, tv_suffix, tv_dec, KPI_PALETTE[2]),
        ("Countries Involved", countries_involved, "", "", 0, KPI_PALETTE[3]),
        ("Sectors Affected", sectors_affected, "", "", 0, KPI_PALETTE[4]),
    ]
    _render_kpi_cards(kpis)

    st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

    # ── Row 2: Trend + Top Targets ─────────────────────────────────────
    chart_left, chart_right = st.columns(2, gap="medium")

    with chart_left:
        st.plotly_chart(
            _chart_trend_over_time(df), use_container_width=True, key="eo_trend"
        )
    with chart_right:
        st.plotly_chart(
            _chart_top_targets(df), use_container_width=True, key="eo_targets"
        )

    # ── Row 3: Sectors + Action Type Breakdown ─────────────────────────
    col_sectors, col_donut = st.columns(2, gap="medium")

    with col_sectors:
        st.plotly_chart(
            _chart_top_sectors(df), use_container_width=True, key="eo_sectors"
        )
    with col_donut:
        st.plotly_chart(
            _chart_action_type_breakdown(df), use_container_width=True, key="eo_types"
        )

    # ── Source note ─────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="source-note">
            Source: <code>tariff_timeline.csv</code> &middot;
            {total_events} official policy actions after filtering out NewsAPI alerts.
            Country codes normalised; <em>Export Control</em> merged into <em>Export Restriction</em>.
            Sectors consolidated into {sectors_affected} primary categories.
        </div>
        """,
        unsafe_allow_html=True,
    )
