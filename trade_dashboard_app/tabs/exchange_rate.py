from __future__ import annotations

from core import *


def render_exchange_rate_tab() -> None:
    df = load_currency_data(CURRENCY_PATH)
    st.markdown(
        """
        <div class="page-title">
            <div>
                <h1>Exchange Rate Pressure</h1>
                <p>Currency movement against the US dollar, volatility, and associations with tariff events.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    base = filter_by_date(df, "currency")
    
    c1, c2, c3 = st.columns([1, 1.4, 0.6])
    with c1:
        countries = sorted(base["country"].dropna().unique())
        selected_countries = st.multiselect("Countries", countries, default=countries, key="currency_countries")
    with c2:
        currencies = sorted(base[base["country"].isin(selected_countries)]["currency"].dropna().unique())
        preferred_currencies = ["CNY", "EUR", "JPY", "VND", "MXN", "CAD"]
        default_currencies = [c for c in preferred_currencies if c in currencies]
        if not default_currencies:
            default_currencies = currencies[:6]
        selected_currencies = st.multiselect(
            "Currencies", currencies, default=default_currencies, key="currency_codes"
        )
    with c3:
        rate_mode = st.radio(
            "Rate view",
            options=["Indexed to 100", "Raw rates"],
            index=0,
            key="rate_mode",
        )

    filtered = base[base["country"].isin(selected_countries) & base["currency"].isin(selected_currencies)].copy()
    if filtered.empty:
        st.info("No currency data match the current filters.")
        return

    vol_work = filtered.dropna(subset=["pct_change_1d"]).copy()
    event_work = vol_work[vol_work["tariff_event_nearby"] == True].copy() if "tariff_event_nearby" in vol_work.columns else None
    normal_work = vol_work[vol_work["tariff_event_nearby"] == False].copy() if "tariff_event_nearby" in vol_work.columns else None

    latest_table = make_latest_table(filtered, ["currency", "country"])
    
    if not latest_table.empty and "pct_change_30d" in latest_table.columns:
        latest_sorted = latest_table.sort_values("pct_change_30d", ascending=False)
        pressure = latest_sorted.iloc[0] if len(latest_sorted) > 0 else None
        relief = latest_sorted.iloc[-1] if len(latest_sorted) > 0 else None
    else:
        pressure, relief = None, None

    event_move = event_work["pct_change_1d"].abs().mean() if event_work is not None and len(event_work) > 0 else None
    normal_move = normal_work["pct_change_1d"].abs().mean() if normal_work is not None and len(normal_work) > 0 else None

    def format_abs_pct(value: float | None) -> str:
        if value is None or pd.isna(value):
            return "n/a"
        return f"{abs(value):.1f}%"

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Currencies covered", f"{filtered['currency'].nunique()}")
    if pressure is not None:
        k2.metric(
            "Highest latest 30-day pressure",
            pressure["currency"],
            format_pct(pressure["pct_change_30d"]),
        )
    else:
        k2.metric("Highest latest 30-day pressure", "N/A", "—")
    
    if relief is not None:
        k3.metric(
            "Lowest latest 30-day pressure",
            relief["currency"],
            format_pct(relief["pct_change_30d"]),
        )
    else:
        k3.metric("Lowest latest 30-day pressure", "N/A", "—")
    
    if event_move is not None:
        if normal_move is not None:
            if abs(event_move - normal_move) < 0.05:
                compare_label = "Similar to normal days"
            else:
                compare_label = f"Normal days: {format_abs_pct(normal_move)}"
            k4.metric(
                "Avg abs event-day move",
                format_abs_pct(event_move),
                compare_label,
            )
        else:
            k4.metric("Avg abs event-day move", format_abs_pct(event_move), "—")
    else:
        k4.metric("Avg abs event-day move", "N/A", "—")

    st.markdown(
        """
        <div style="background-color: #f7f9fb; border-left: 3px solid #227c74; padding: 0.8rem; margin-bottom: 1rem; border-radius: 4px;">
        <p style="margin: 0; color: #667085; font-size: 0.9rem;"><strong>Definition:</strong> Exchange-rate pressure is measured by the latest 30-day percentage change against USD. Positive values indicate an upward movement in the exchange-rate series. When the series is quoted as local currency per USD, this corresponds to local-currency depreciation.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    indexed = rate_mode == "Indexed to 100"
    st.plotly_chart(make_currency_rate_chart(filtered, indexed=indexed))
    if indexed:
        st.caption("Indexed values allow fair comparison across currencies with different exchange-rate scales.")
    else:
        st.caption("Raw exchange-rate levels show local currency units per US dollar. Note: currencies at different scale levels.")

    st.plotly_chart(make_currency_volatility_chart(filtered))
    st.caption("Volatility is computed from percentage changes rather than raw exchange-rate levels to avoid scale distortion.")

    st.plotly_chart(make_currency_event_box(filtered))
    st.caption(
        "Magnitude of one-day currency movements near tariff events versus normal days. "
        "This shows association, not causation."
    )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(make_currency_latest_pressure(filtered))
        st.caption(
            "Latest 30-day pressure is measured by the most recent available 30-day percentage change against USD. "
            "Positive bars indicate positive latest 30-day percentage change; negative bars indicate negative latest 30-day percentage change."
        )
    with right:
        st.plotly_chart(make_currency_change_heatmap(filtered))
        st.caption(
            "Blue/red intensity shows positive/negative average 30-day percentage changes by year. "
            "Values are based on percentage changes, not raw exchange-rate levels."
        )

    st.markdown(
        f"""
        <div class="source-note">
            Source: <code>{CURRENCY_PATH}</code>. Higher <code>rate_vs_usd</code> means more local-currency units per US dollar.
        </div>
        """,
        unsafe_allow_html=True,
    )
