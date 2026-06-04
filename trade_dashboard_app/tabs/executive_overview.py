from __future__ import annotations

import math

from core import *


# ── Colour palette ──────────────────────────────────────────────────────
ACCENT_TEAL = "#009E73"
ACCENT_CORAL = "#D55E00"
ACCENT_GOLD = "#E69F00"
ACCENT_BLUE = "#0072B2"
ACCENT_PURPLE = "#CC79A7"
ACCENT_SIMPLE = "#20242a"
GRID_COLOR = "#e9edf3"

KPI_PALETTE = [ACCENT_SIMPLE, ACCENT_BLUE, ACCENT_GOLD, ACCENT_TEAL, ACCENT_PURPLE]
BAR_COLOR_SCALE = [
    [0, "#e7f1f7"],
    [0.35, "#9ecae1"],
    [0.65, "#4292c6"],
    [1, ACCENT_BLUE],
]

TYPE_ACCENT = {
    "New Tariff": ACCENT_TEAL,
    "Escalation": ACCENT_CORAL,
    "Retaliation": ACCENT_GOLD,
    "Reduction": ACCENT_BLUE,
    "Universal Baseline": ACCENT_PURPLE,
    "Expansion": "#56B4E9",
    "Export Restriction": "#332288",
}

COUNTRY_FLOW_POSITIONS = {
    "CAN": (0.08, 0.82),
    "USA": (0.10, 0.56),
    "MEX": (0.14, 0.24),
    "GBR": (0.39, 0.79),
    "EU27": (0.52, 0.62),
    "IND": (0.70, 0.28),
    "CHN": (0.84, 0.59),
    "JPN": (0.96, 0.68),
    "GLOBAL": (0.50, 0.96),
}


def _geographic_flow_layout(
    nodes: list[str],
    edges: pd.DataFrame,
) -> dict[str, tuple[float, float]]:
    """Deterministic, geography-anchored layout for the country flow graph."""
    positions = {
        node: COUNTRY_FLOW_POSITIONS[node]
        for node in nodes
        if node in COUNTRY_FLOW_POSITIONS
    }
    fallback_nodes = [node for node in nodes if node not in positions]
    for idx, node in enumerate(fallback_nodes):
        angle = 2 * math.pi * idx / max(len(fallback_nodes), 1)
        positions[node] = (
            0.50 + 0.32 * math.cos(angle),
            0.52 + 0.26 * math.sin(angle),
        )

    anchors = positions.copy()
    if len(nodes) <= 2:
        return positions

    edge_pairs = [
        (row["imposing_clean"], row["target_clean"], row["events"])
        for _, row in edges.iterrows()
        if row["imposing_clean"] in positions and row["target_clean"] in positions
    ]
    max_weight = max((weight for _, _, weight in edge_pairs), default=1)
    ideal_length = 0.38

    for _ in range(180):
        forces = {node: [0.0, 0.0] for node in nodes}

        for i, left in enumerate(nodes):
            lx, ly = positions[left]
            for right in nodes[i + 1:]:
                rx, ry = positions[right]
                dx = lx - rx
                dy = ly - ry
                dist = math.hypot(dx, dy) or 0.001
                force = 0.0017 / (dist * dist)
                fx = dx / dist * force
                fy = dy / dist * force
                forces[left][0] += fx
                forces[left][1] += fy
                forces[right][0] -= fx
                forces[right][1] -= fy

        for source, target, weight in edge_pairs:
            sx, sy = positions[source]
            tx, ty = positions[target]
            dx = tx - sx
            dy = ty - sy
            dist = math.hypot(dx, dy) or 0.001
            weighted_pull = 0.034 + 0.028 * (weight / max_weight) ** 0.5
            force = weighted_pull * (dist - ideal_length)
            fx = dx / dist * force
            fy = dy / dist * force
            forces[source][0] += fx
            forces[source][1] += fy
            forces[target][0] -= fx
            forces[target][1] -= fy

        for node in nodes:
            x, y = positions[node]
            ax, ay = anchors[node]
            forces[node][0] += (ax - x) * 0.075
            forces[node][1] += (ay - y) * 0.075

        for node in nodes:
            fx, fy = forces[node]
            step = min(math.hypot(fx, fy), 0.012)
            if step <= 0:
                continue
            scale = step / (math.hypot(fx, fy) or 1)
            x, y = positions[node]
            positions[node] = (
                min(0.94, max(0.08, x + fx * scale)),
                min(0.92, max(0.20, y + fy * scale)),
            )

    return positions

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
            padding: 0.95rem 0.7rem 0.85rem;
            text-align: center;
            min-height: 92px;
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
            font-size: 1.55rem;
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
    components.html(html, height=112, scrolling=False)


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
            marker_color=ACCENT_BLUE,
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
        height=340,
        margin=dict(l=0, r=10, t=56, b=0),
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
        xaxis=dict(title="Year", dtick=1, gridcolor=GRID_COLOR),
        yaxis=dict(
            title=dict(text="Number of Events", font=dict(color=ACCENT_BLUE)),
            tickfont=dict(color=ACCENT_BLUE),
            gridcolor=GRID_COLOR,
            rangemode="tozero",
        ),
        yaxis2=dict(
            title=dict(text="Average Tariff Rate (%)", font=dict(color=ACCENT_CORAL)),
            tickfont=dict(color=ACCENT_CORAL),
            overlaying="y",
            side="right",
            showgrid=False,
            rangemode="tozero",
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
        labels={"events": "Number of tariff actions", "label": "Target country"},
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Events: %{x}<extra></extra>",
        texttemplate="%{x}",
        textposition="outside",
        textfont=dict(size=12, color="#444"),
    )
    fig.update_layout(
        title=dict(text="Most Frequently Targeted Countries", font=dict(size=17)),
        height=260,
        margin=dict(l=0, r=40, t=56, b=0),
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
        xaxis=dict(gridcolor=GRID_COLOR, title="Number of tariff actions", rangemode="tozero"),
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
            [0, "#fff2df"],
            [0.35, "#f1c27d"],
            [0.65, "#e69f00"],
            [1, ACCENT_CORAL],
        ],
        labels={"events": "Number of tariff actions", "sector_clean": "Sector"},
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Events: %{x}<extra></extra>",
        texttemplate="%{x}",
        textposition="outside",
        textfont=dict(size=12, color="#444"),
    )
    fig.update_layout(
        title=dict(text="Top Affected Sectors", font=dict(size=17)),
        height=260,
        margin=dict(l=0, r=40, t=56, b=0),
        coloraxis_showscale=False,
        yaxis=dict(tickfont=dict(size=11)),
        xaxis=dict(gridcolor=GRID_COLOR, title="Number of tariff actions", rangemode="tozero"),
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
            textinfo="percent",
            textposition="inside",
            textfont=dict(size=11, color="#ffffff"),
            hovertext=hover_texts,
            hoverinfo="text",
            pull=[0.03 if i == 0 else 0 for i in range(len(type_counts))],
        )
    )

    fig.update_layout(
        title=dict(text="Action Type Distribution", font=dict(size=17)),
        height=260,
        margin=dict(l=10, r=130, t=56, b=10),
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1.02,
            y=0.5,
            xanchor="left",
            yanchor="middle",
            font=dict(size=11),
        ),
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


# ── Chart E: Country Action Flow (node graph) ─────────────────────────
def _chart_country_action_flow(
    df: pd.DataFrame,
    year_filter: int | None,
) -> go.Figure:
    work = df.copy()
    if year_filter is not None:
        work = work[work["year"] == year_filter]

    flow = (
        work.groupby(["imposing_clean", "target_clean"], as_index=False)
        .size()
        .rename(columns={"size": "events"})
    )
    if flow.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No tariff actions for the selected year.",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=13, color="#667085"),
        )
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=40, b=0))
        return fig

    involvement = pd.concat(
        [
            flow[["imposing_clean", "events"]].rename(
                columns={"imposing_clean": "country"}
            ),
            flow[["target_clean", "events"]].rename(
                columns={"target_clean": "country"}
            ),
        ],
        ignore_index=True,
    )
    top_nodes = (
        involvement.groupby("country", as_index=False)["events"]
        .sum()
        .sort_values("events", ascending=False)
        .head(12)
    )
    node_set = set(top_nodes["country"].tolist())
    flow = flow[
        flow["imposing_clean"].isin(node_set)
        & flow["target_clean"].isin(node_set)
    ].copy()

    if flow.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Not enough data to show a country network for this year.",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=13, color="#667085"),
        )
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=40, b=0))
        return fig

    top_edges = flow.sort_values("events", ascending=False).head(18)
    max_edge = top_edges["events"].max() if not top_edges.empty else 1
    min_edge = top_edges["events"].min() if not top_edges.empty else 0

    nodes = sorted(
        set(top_edges["imposing_clean"]) | set(top_edges["target_clean"]),
        key=lambda c: (
            top_nodes.set_index("country")["events"].get(c, 0),
            entity_label(c),
        ),
        reverse=True,
    )
    node_labels = [entity_label(c) for c in nodes]
    out_degree = top_edges.groupby("imposing_clean")["events"].sum()
    in_degree = top_edges.groupby("target_clean")["events"].sum()
    weighted_degree = {
        node: out_degree.get(node, 0) + in_degree.get(node, 0)
        for node in nodes
    }
    net_outgoing = {
        node: out_degree.get(node, 0) - in_degree.get(node, 0)
        for node in nodes
    }

    positions = _geographic_flow_layout(nodes, top_edges)

    max_degree = max(weighted_degree.values()) if weighted_degree else 1
    sizes = [
        15 + 18 * (weighted_degree[node] / max_degree) ** 0.5
        for node in nodes
    ]

    fig = go.Figure()

    for _, row in top_edges.iterrows():
        source = row["imposing_clean"]
        target = row["target_clean"]
        start_x, start_y = positions[source]
        end_x, end_y = positions[target]
        dx = end_x - start_x
        dy = end_y - start_y
        dist = math.hypot(dx, dy) or 1
        offset = 0.06
        sx = start_x + dx / dist * offset
        sy = start_y + dy / dist * offset
        tx = end_x - dx / dist * offset
        ty = end_y - dy / dist * offset
        if max_edge > min_edge:
            edge_width = 1 + (row["events"] - min_edge) / (max_edge - min_edge) * 3
        else:
            edge_width = 1.8

        # Draw a curved edge and a small arrowhead along the curve tangent.
        curve = 0.12 if source < target else -0.12
        mid_x = (sx + tx) / 2
        mid_y = (sy + ty) / 2
        norm_x = -dy / dist
        norm_y = dx / dist
        ctrl_x = mid_x + norm_x * curve
        ctrl_y = mid_y + norm_y * curve
        edge_color = "rgba(0, 114, 178, 0.34)"
        steps = 18
        xs = []
        ys = []
        for step in range(steps + 1):
            t = step / steps
            xs.append((1 - t) ** 2 * sx + 2 * (1 - t) * t * ctrl_x + t ** 2 * tx)
            ys.append((1 - t) ** 2 * sy + 2 * (1 - t) * t * ctrl_y + t ** 2 * ty)
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines",
                line=dict(width=edge_width, color=edge_color),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        tangent_x = tx - ctrl_x
        tangent_y = ty - ctrl_y
        tangent_len = math.hypot(tangent_x, tangent_y) or 1
        unit_x = tangent_x / tangent_len
        unit_y = tangent_y / tangent_len
        perp_x = -unit_y
        perp_y = unit_x
        head_len = 0.028
        head_spread = 0.012
        base_x = tx - unit_x * head_len
        base_y = ty - unit_y * head_len
        left_x = base_x + perp_x * head_spread
        left_y = base_y + perp_y * head_spread
        right_x = base_x - perp_x * head_spread
        right_y = base_y - perp_y * head_spread
        fig.add_trace(
            go.Scatter(
                x=[left_x, tx, right_x],
                y=[left_y, ty, right_y],
                mode="lines",
                line=dict(width=max(1.2, edge_width * 0.8), color=edge_color),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[ctrl_x],
                y=[ctrl_y],
                mode="markers",
                marker=dict(size=max(8, edge_width * 4), color="rgba(0,0,0,0)"),
                hovertext=(
                    f"<b>{entity_label(source)} -> {entity_label(target)}</b><br>"
                    f"Tariff actions: {row['events']}"
                ),
                hoverinfo="text",
                showlegend=False,
            )
        )

    x_nodes = [positions[node][0] for node in nodes]
    y_nodes = [positions[node][1] for node in nodes]
    hover_nodes = [
        f"<b>{label}</b><br>"
        f"Weighted degree: {weighted_degree[node]}<br>"
        f"Outgoing actions: {out_degree.get(node, 0)}<br>"
        f"Incoming actions: {in_degree.get(node, 0)}"
        for node, label in zip(nodes, node_labels)
    ]

    fig.add_trace(
        go.Scatter(
            x=x_nodes,
            y=y_nodes,
            mode="markers+text",
            text=node_labels,
            textposition="bottom center",
            textfont=dict(size=10, color="#1f2933"),
            marker=dict(
                size=sizes,
                color=[net_outgoing[node] for node in nodes],
                colorscale=[
                    [0, ACCENT_CORAL],
                    [0.5, "#cbd5e1"],
                    [1, ACCENT_BLUE],
                ],
                cmid=0,
                line=dict(color="#ffffff", width=1.2),
                colorbar=dict(
                    title=dict(text="Net outgoing", font=dict(size=10)),
                    thickness=8,
                    len=0.68,
                    x=1.02,
                    tickfont=dict(size=10),
                ),
            ),
            hovertext=hover_nodes,
            hoverinfo="text",
            showlegend=False,
        )
    )

    year_suffix = "All years" if year_filter is None else f"{year_filter}"
    fig.update_layout(
        title=dict(
            text=(
                f"Tariff Action Flows by Country ({year_suffix})"
                "<br><sup>Geographic relative layout; node size = weighted degree, edge width = action count.</sup>"
            ),
            font=dict(size=17),
        ),
        height=340,
        margin=dict(l=0, r=28, t=70, b=8),
        plot_bgcolor="#ffffff",
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1]),
    )
    return fig


# ── Main render function ───────────────────────────────────────────────
def render_executive_overview_tab() -> None:
    raw = load_tariff_data(TARIFF_PATH)
    df = _clean_overview_data(raw)

    # ── Page header ─────────────────────────────────────────────────────
    st.markdown(
        """
        <style>
        .eo-page-title {
            margin-top: -0.7rem;
            margin-bottom: 0.35rem;
            padding-bottom: 0.28rem;
        }
        .eo-compact-title h1 {
            font-size: 1.35rem;
            line-height: 1.2;
            margin: 0;
        }
        .eo-compact-title p {
            margin: 0;
            color: #667085;
            font-size: 0.82rem;
            line-height: 1.15;
        }
        </style>
        <div class="page-title eo-page-title">
            <div class="eo-compact-title">
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

    year_options = ["All years"] + sorted(df["year"].dropna().unique().tolist())
    year_choice = st.selectbox(
        "Filter executive overview by year",
        options=year_options,
        index=0,
        help="Updates KPIs, action mix, sectors, and the country action network.",
    )
    selected_year = None if year_choice == "All years" else int(year_choice)
    filtered_df = df if selected_year is None else df[df["year"] == selected_year].copy()

    # ── Compute KPI metrics ─────────────────────────────────────────────
    total_events = len(filtered_df)
    avg_rate = filtered_df["tariff_rate_pct"].mean()
    total_trade_value = filtered_df["estimated_trade_value_usd_bn"].sum()

    all_countries = set(filtered_df["imposing_clean"].dropna().unique()) | set(
        filtered_df["target_clean"].dropna().unique()
    )
    countries_involved = len(all_countries)
    sectors_affected = filtered_df["sector_clean"].nunique()

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

    st.markdown("<div style='height: 0.15rem;'></div>", unsafe_allow_html=True)

    # ── Filters ───────────────────────────────────────────────────────
    # ── Row 2: Trend + Targets + Sectors ───────────────────────────────
    col_trend, col_flow = st.columns(2, gap="medium")

    with col_trend:
        st.plotly_chart(
            _chart_trend_over_time(filtered_df), use_container_width=True, key="eo_trend"
        )
    with col_flow:
        st.plotly_chart(
            _chart_country_action_flow(df, selected_year),
            use_container_width=True,
            key="eo_country_flow",
        )

    # ── Row 3: Action Type + Country action network ───────────────────
    col_donut, col_sectors = st.columns(2, gap="medium")

    with col_donut:
        st.plotly_chart(
            _chart_action_type_breakdown(filtered_df), use_container_width=True, key="eo_types"
        )
    with col_sectors:
        st.plotly_chart(
            _chart_top_sectors(filtered_df), use_container_width=True, key="eo_sectors"
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
