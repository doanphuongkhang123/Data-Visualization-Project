import streamlit as st

from core import configure_page
from tabs.executive_overview import render_executive_overview_tab
from tabs.financial_market import render_financial_market_tab
from tabs.inflation_currency import render_inflation_currency_tab
from tabs.sector_impact import render_sector_impact_tab
from tabs.tariff_tensions import render_tariff_tensions_tab


configure_page()

tabs = st.tabs(
    [
        "Executive Overview",
        "Trade and Macro Impact",
        "Financial Market Reaction",
        "Sectoral Impact",
        "Inflation & Currency Response",
    ]
)
with tabs[0]:
    render_executive_overview_tab()
with tabs[1]:
    render_tariff_tensions_tab()
with tabs[2]:
    render_financial_market_tab()
with tabs[3]:
    render_sector_impact_tab()
with tabs[4]:
    render_inflation_currency_tab()
