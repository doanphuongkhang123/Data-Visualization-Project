# Global Trade Dashboard

Prototype inspired by WTO trade dashboards.

Current tabs:

- `Trade Volume`: annual goods and services trade overview.
- `Global Tariff Tensions`: tariff events, retaliation, sector exposure, maps, rate distributions, and a directed tariff network.
- `Financial Market Reaction`: stock-index performance, event-day return distributions, volatility, and annual return heatmaps.
- `Exchange Rate Pressure`: currency movement versus USD, volatility, event-day moves, and 30-day pressure.
- `Sectoral Impact`: sector ETF performance, latest sector heatmap, tariff-sensitivity returns, and volatility.
- `Vietnam Impact`: Vietnam trade/macro indicators, VND pressure, VN-Index performance, and direct tariff-event checks.
- `Long-term Macro Adjustment`: annual macro indicators, period distributions, country heatmaps, correlations, and US monthly adjustment series.

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
