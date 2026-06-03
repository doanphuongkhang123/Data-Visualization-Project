import streamlit as st

from core import configure_page
from tabs.executive_overview import render_executive_overview_tab
from tabs.exchange_rate import render_exchange_rate_tab
from tabs.financial_market import render_financial_market_tab
from tabs.macro_adjustment import render_macro_adjustment_tab
from tabs.sector_impact import render_sector_impact_tab
from tabs.tariff_tensions import render_tariff_tensions_tab
from tabs.trade_volume import render_trade_volume_tab
from tabs.vietnam_impact import render_vietnam_impact_tab


configure_page()

tabs = st.tabs(
    [
        "Executive Overview",
        "Trade Volume",
        "Trade and Macro Impact",
        "Financial Market Reaction",
        "Exchange Rate Pressure",
        "Sectoral Impact",
        "Vietnam Impact",
        "Long-term Macro Adjustment",
    ]
)
with tabs[0]:
    render_executive_overview_tab()
with tabs[1]:
    render_trade_volume_tab()
with tabs[2]:
    render_tariff_tensions_tab()
with tabs[3]:
    render_financial_market_tab()
with tabs[4]:
    render_exchange_rate_tab()
with tabs[5]:
    render_sector_impact_tab()
with tabs[6]:
    render_vietnam_impact_tab()
with tabs[7]:
    render_macro_adjustment_tab()
