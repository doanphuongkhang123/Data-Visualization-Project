# EDA Summary for `new/` CSV Files

Generated: 2026-06-03 10:46:42

## Dataset Inventory

| file                      | rows  | columns | numeric_columns | categorical_columns | missing_cells | missing_pct | duplicate_rows | time_range               |
| ------------------------- | ----- | ------- | --------------- | ------------------- | ------------- | ----------- | -------------- | ------------------------ |
| stock_market_reaction.csv | 34838 | 16      | 11              | 5                   | 1598          | 0.29        | 0              | 2018-01-01 to 2026-05-29 |
| sector_impact.csv         | 33808 | 15      | 9               | 6                   | 256           | 0.05        | 0              | 2018-01-02 to 2026-05-29 |
| currency_impact.csv       | 32833 | 10      | 6               | 4                   | 1095          | 0.33        | 0              | 2018-01-01 to 2026-05-29 |
| inflation_response.csv    | 1897  | 11      | 3               | 8                   | 182           | 0.87        | 0              | 2015-01-01 to 2026-04-01 |
| trade_volume_annual.csv   | 1363  | 9       | 3               | 6                   | 135           | 1.1         | 0              | 2015 to 2025             |
| column_metadata.csv       | 62    | 4       | 0               | 4                   | 0             | 0.0         | 0              |                          |
| tariff_timeline.csv       | 60    | 16      | 5               | 11                  | 36            | 3.75        | 0              | 2018-03-08 to 2026-05-27 |

## Key EDA Findings

- The folder contains seven CSV files covering tariff events, annual trade/macro indicators, currency rates, sector ETFs, stock indices, inflation, and column metadata.
- Largest table: `stock_market_reaction.csv` with 34,838 rows.
- The analytical shape is mostly time-series plus event data: daily financial market data, monthly inflation data, annual macro/trade data, and discrete tariff announcements.
- The dashboard-ready columns are already documented in `column_metadata.csv`, which makes it a good source for labels, tooltips, and field descriptions.
- Several files include missing values in lagged/rolling fields, which is expected at the beginning of each time series.

## Applying the 9 Course Chapters

### Chapter 1: Overview of data visualization
Used for defining the project purpose: explain trade-war effects through tariffs, trade volumes, markets, currencies, sectors, and inflation. The charts support exploration and comparison rather than a single static conclusion.

### Chapter 2: Visual models and encoding
Nominal variables: country, currency, sector, tariff type, tariff sensitivity, period/era. Quantitative variables: values, returns, volatility, tariff rates, affected trade value. Encodings used: position for time/category, color for grouping or intensity, size for affected trade value, and heatmap color for matrix values.

### Chapter 3: Graphical perception
Used pre-attentive color differences in heatmaps and event/status colors. Magnitude estimation is supported through common axes in line/bar charts and color scales in heatmaps. Multiple encodings are used carefully: e.g. tariff timeline uses x-position, y-position, color, and bubble size.

### Chapter 4: Visualization for multi-dimensional data
Used the most heavily. Amounts: bars and choropleths. Distributions: histograms, boxplots, violins. Proportions: dataset coverage and event group comparisons. Relationships: tariff imposing-target heatmap and event proximity comparisons. Trends: line charts for annual, monthly, and daily time series.

### Chapter 5: Visualization for graphs
Only lightly applicable. The tariff event table can be interpreted as a directed relationship from imposing country to target country; the heatmap is used instead of a node-link graph to avoid clutter.

### Chapter 6: Principles of figure design
Applied proportional ink in bars and choropleths, avoided 3D, used titles and captions, used multi-panel/faceted views for dense time-series data, and used sequential/diverging color scales where appropriate.

### Chapter 7: Map visualization
Applicable to country-level trade indicators. The EDA report includes choropleth maps for latest-year exports/imports/trade share when ISO mappings are available.

### Chapter 8: Interactive visualization
The generated Plotly HTML report supports hover details, zooming, legend selection, and standalone chart inspection. These interactions support filtering and view transformation before building the final dashboard.

### Chapter 9: Storytelling with data
The suggested narrative is: tariff actions create policy shocks; trade and macro indicators show annual structural effects; markets/currencies/sectors show faster reactions; inflation gives downstream consumer/producer impact.

## Recommended Dashboard Tabs

1. Trade volume overview: annual country map, ranking table, regional bars, and country trends.
2. Tariff timeline: event timeline, affected sectors, retaliation, imposing-target relationship.
3. Market reaction: stock indices and sector impacts near tariff events.
4. Currency and inflation response: exchange-rate movements and CPI/PPI comparisons.
5. Methodology/data quality: source files, missingness, coverage, and metadata.
