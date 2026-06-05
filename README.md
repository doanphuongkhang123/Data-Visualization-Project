# Global Trade Dashboard

Prototype inspired by WTO trade dashboards.

Current tabs:

- `Executive Overview`: headline trade-war context and cross-dataset indicators.
- `Trade and Macro Impact`: tariff events, retaliation, sector exposure, maps, rate distributions, and a directed tariff network.
- `Financial Market Reaction`: stock-index performance, event-day return distributions, volatility, and annual return heatmaps.
- `Sectoral Impact`: sector ETF performance, latest sector heatmap, tariff-sensitivity returns, and volatility.
- `Inflation & Currency Response`: US price pressure, US-China trade flows, US total trade balance, currency rates versus USD, rolling 7-day volatility, and currency movement around tariff events.

## Installations
```bash
pip install -r trade_dashboard_app/requirements.txt
```

## Run

```bash
python3 -m streamlit run trade_dashboard_app/app.py
```

The app reads:

```text
new/trade_volume_annual.csv
new/tariff_timeline.csv
new/stock_market_reaction.csv
new/currency_impact.csv
new/sector_impact.csv
new/inflation_response.csv
```
