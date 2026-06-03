# Exploratory Data Analysis Report: sector_impact.csv

**Generated:** 2026-06-03 10:42:56

---

## Basic Information

- **Filename:** `sector_impact.csv`
- **Full Path:** `/Users/khang/Downloads/2025.2/DV/draft/new/sector_impact.csv`
- **File Size:** 6.88 MB (7,218,113 bytes)
- **Last Modified:** 2026-05-31T22:32:38
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
    15
  ],
  "columns": [
    "date",
    "country",
    "sector",
    "sector_label",
    "ticker",
    "tariff_sensitivity",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "daily_return_pct",
    "weekly_return_pct",
    "indexed_to_100",
    "volatility_10d"
  ],
  "dtypes": {
    "date": "object",
    "country": "object",
    "sector": "object",
    "sector_label": "object",
    "ticker": "object",
    "tariff_sensitivity": "object",
    "open": "float64",
    "high": "float64",
    "low": "float64",
    "close": "float64",
    "volume": "int64",
    "daily_return_pct": "float64",
    "weekly_return_pct": "float64",
    "indexed_to_100": "float64",
    "volatility_10d": "float64"
  },
  "missing_values": {
    "date": 0,
    "country": 0,
    "sector": 0,
    "sector_label": 0,
    "ticker": 0,
    "tariff_sensitivity": 0,
    "open": 0,
    "high": 0,
    "low": 0,
    "close": 0,
    "volume": 0,
    "daily_return_pct": 5,
    "weekly_return_pct": 25,
    "indexed_to_100": 0,
    "volatility_10d": 50
  },
  "summary_statistics": {
    "open": {
      "count": 10000.0,
      "mean": 64.5381510357682,
      "std": 35.801842821031336,
      "min": 9.380215806330437,
      "25%": 36.1359934158708,
      "50%": 58.45021654054973,
      "75%": 88.11427796294225,
      "max": 189.3300018310547
    },
    "high": {
      "count": 10000.0,
      "mean": 65.03283869771387,
      "std": 36.02617345372024,
      "min": 9.912262250273614,
      "25%": 36.48850106920054,
      "50%": 58.85000351201745,
      "75%": 88.7061889296214,
      "max": 191.6300048828125
    },
    "low": {
      "count": 10000.0,
      "mean": 64.01404802136707,
      "std": 35.55557455153331,
      "min": 8.82118195581966,
      "25%": 35.80308657673029,
      "50%": 57.915635843662685,
      "75%": 87.39477317839588,
      "max": 189.1999969482422
    },
    "close": {
      "count": 10000.0,
      "mean": 64.54695557193756,
      "std": 35.80985154919104,
      "min": 9.245277404785156,
      "25%": 36.14645576477051,
      "50%": 58.3140811920166,
      "75%": 88.05218696594238,
      "max": 191.02000427246097
    },
    "volume": {
      "count": 10000.0,
      "mean": 18856694.6,
      "std": 17530817.641541168,
      "min": 1771400.0,
      "25%": 8850800.0,
      "50%": 12569200.0,
      "75%": 21063750.0,
      "max": 198713400.0
    },
    "daily_return_pct": {
      "count": 9995.0,
      "mean": 0.061746823117418165,
      "std": 1.595801500980002,
      "min": -20.141182545541568,
      "25%": -0.6853113381968423,
      "50%": 0.1099881115791179,
      "75%": 0.8635372010706743,
      "max": 16.037330091237333
    },
    "weekly_return_pct": {
      "count": 9975.0,
      "mean": 0.3000446355496147,
      "std": 3.4189372202803465,
      "min": -34.554744487054776,
      "25%": -1.3935802281051457,
      "50%": 0.4217021906657292,
      "75%": 2.14626870346587,
      "max": 23.895712389591385
    },
    "indexed_to_100": {
      "count": 10000.0,
      "mean": 164.468464263926,
      "std": 81.3602339148128,
      "min": 35.907804010702435,
      "25%": 106.0708974606839,
      "50%": 146.60640545780274,
      "75%": 191.1279459780644,
      "max": 639.4420436249159
    },
    "volatility_10d": {
      "count": 9950.0,
      "mean": 1.3495698882494958,
      "std": 0.8699986358841466,
      "min": 0.1968483667027078,
      "25%": 0.8442896740171288,
      "50%": 1.1519302320138398,
      "75%": 1.5885874144786094,
      "max": 10.529393212653632
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