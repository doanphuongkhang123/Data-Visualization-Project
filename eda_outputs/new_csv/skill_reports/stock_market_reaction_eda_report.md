# Exploratory Data Analysis Report: stock_market_reaction.csv

**Generated:** 2026-06-03 10:42:56

---

## Basic Information

- **Filename:** `stock_market_reaction.csv`
- **Full Path:** `/Users/khang/Downloads/2025.2/DV/draft/new/stock_market_reaction.csv`
- **File Size:** 7.42 MB (7,781,658 bytes)
- **Last Modified:** 2026-05-31T22:32:40
- **Extension:** `.csv`

## File Type

- **Category:** General Scientific
- **Description:** Comma-Separated Values

## Format Reference

### .csv - Comma-Separated Values
**Description:** Plain text tabular data
**Typical Data:** Experimental measurements, results tables
**Use Cases:** Universal data exchange, spreadsheet export
**Python Libraries:**
- `pandas`: `pd.read_csv('file.csv')`
- `csv`: Built-in module
- `polars`: High-performance CSV reading
- `numpy`: `np.loadtxt()` or `np.genfromtxt()`
**EDA Approach:**
- Row and column counts
- Data type inference
- Missing value patterns and frequency
- Column statistics (numeric: mean, std; categorical: frequencies)
- Outlier detection
- Correlation matrix
- Duplicate row detection
- Header and index validation
- Encoding issues detection



*Reference: general_scientific_formats.md*

## Data Analysis

### Summary Statistics

```json
{
  "shape": [
    10000,
    16
  ],
  "columns": [
    "date",
    "country",
    "index_name",
    "ticker",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "daily_return_pct",
    "weekly_return_pct",
    "ma_20d",
    "ma_50d",
    "volatility_20d",
    "indexed_to_100",
    "tariff_event_nearby"
  ],
  "dtypes": {
    "date": "object",
    "country": "object",
    "index_name": "object",
    "ticker": "object",
    "open": "float64",
    "high": "float64",
    "low": "float64",
    "close": "float64",
    "volume": "int64",
    "daily_return_pct": "float64",
    "weekly_return_pct": "float64",
    "ma_20d": "float64",
    "ma_50d": "float64",
    "volatility_20d": "float64",
    "indexed_to_100": "float64",
    "tariff_event_nearby": "bool"
  },
  "missing_values": {
    "date": 0,
    "country": 0,
    "index_name": 0,
    "ticker": 0,
    "open": 0,
    "high": 0,
    "low": 0,
    "close": 0,
    "volume": 0,
    "daily_return_pct": 5,
    "weekly_return_pct": 25,
    "ma_20d": 95,
    "ma_50d": 245,
    "volatility_20d": 100,
    "indexed_to_100": 0,
    "tariff_event_nearby": 0
  },
  "summary_statistics": {
    "open": {
      "count": 10000.0,
      "mean": 15426.550170141601,
      "std": 12662.670761351226,
      "min": 2290.7099609375,
      "25%": 3592.9049072265625,
      "50%": 11635.0849609375,
      "75%": 25811.51953125,
      "max": 50773.91015625
    },
    "high": {
      "count": 10000.0,
      "mean": 15522.186578564453,
      "std": 12731.682079992019,
      "min": 2300.72998046875,
      "25%": 3611.2872924804688,
      "50%": 11725.61474609375,
      "75%": 25951.39794921875,
      "max": 51094.1796875
    },
    "low": {
      "count": 10000.0,
      "mean": 15320.840691430663,
      "std": 12586.540209411918,
      "min": 2191.860107421875,
      "25%": 3573.0674438476562,
      "50%": 11494.14501953125,
      "75%": 25608.90234375,
      "max": 50698.26953125
    },
    "close": {
      "count": 10000.0,
      "mean": 15426.631148852539,
      "std": 12662.93737366694,
      "min": 2237.39990234375,
      "25%": 3592.5696411132812,
      "50%": 11624.294921875,
      "75%": 25790.97705078125,
      "max": 51032.4609375
    },
    "volume": {
      "count": 10000.0,
      "mean": 2406695227.3,
      "std": 2405708975.8466744,
      "min": 0.0,
      "25%": 285432500.0,
      "50%": 1958685000.0,
      "75%": 4083582500.0,
      "max": 16308730000.0
    },
    "daily_return_pct": {
      "count": 9995.0,
      "mean": 0.035466793687388386,
      "std": 1.2850759913160819,
      "min": -12.926545507355424,
      "25%": -0.5400941981700824,
      "50%": 0.0698223641654394,
      "75%": 0.6754358720101883,
      "max": 12.163161348672212
    },
    "weekly_return_pct": {
      "count": 9975.0,
      "mean": 0.16982468709383078,
      "std": 2.724160629169586,
      "min": -18.837745656808924,
      "25%": -1.2491208223378627,
      "50%": 0.3386530232040607,
      "75%": 1.6786088015611988,
      "max": 21.88687926800941
    },
    "ma_20d": {
      "count": 9905.0,
      "mean": 15406.41730928439,
      "std": 12632.215091047972,
      "min": 2515.648962402344,
      "25%": 3576.9215087890625,
      "50%": 11572.624072265626,
      "75%": 25775.7384765625,
      "max": 49916.8048828125
    },
    "ma_50d": {
      "count": 9755.0,
      "mean": 15377.183146558958,
      "std": 12589.84207515199,
      "min": 2570.211865234375,
      "25%": 3566.396484375,
      "50%": 11676.815,
      "75%": 25819.56673828125,
      "max": 49138.25578125
    },
    "volatility_20d": {
      "count": 9900.0,
      "mean": 1.1269538488363737,
      "std": 0.6387689938112077,
      "min": 0.3139217049178392,
      "25%": 0.7360234701577538,
      "50%": 0.9765298298463896,
      "75%": 1.352486978687943,
      "max": 6.588389507767426
    },
    "indexed_to_100": {
      "count": 10000.0,
      "mean": 135.09626219888113,
      "std": 57.84511718872693,
      "min": 48.13000185165758,
      "25%": 95.6283413404101,
      "50%": 112.93745243469768,
      "75%": 164.6214134605216,
      "max": 384.9436914548027
    }
  }
}
```

## Recommendations for Further Analysis

Based on the file type (`.csv`), consider the following analyses:

- Statistical distribution analysis
- Missing value imputation strategies
- Correlation analysis between variables
- Outlier detection and handling
- Dimensionality reduction (PCA, t-SNE)

---
*This report was generated by the exploratory-data-analysis skill.*