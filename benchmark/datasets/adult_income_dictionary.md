# Adult Census Income Data Dictionary

## 1. Overview
The Adult Census Income dataset is derived from 1994 United States Census Bureau survey data.
It serves as an analytical benchmark in Athena for testing socio-economic demographic segmentation,
workplace hours disparity analysis, and binary classification of income thresholds.

- **Dataset ID:** `adult_income`
- **Primary Target:** `high_income` (binary classification: 1 = income > \$50K/yr, 0 = <= \$50K/yr)
- **Granularity:** One record per adult survey respondent

---

## 2. Feature Schema & Column Definitions

| Column Name | Physical Type | Semantic Type | Description | Values / Range |
| :--- | :--- | :--- | :--- | :--- |
| `age` | `BIGINT` | Continuous | Age of the individual in years | 17 - 90 |
| `workclass` | `VARCHAR` | Categorical | Employment sector of the individual | `Private`, `Self-emp`, `Gov`, `Federal-gov` |
| `education` | `VARCHAR` | Ordinal | Highest formal education level completed | `HS-grad`, `Bachelors`, `Masters`, `Doctorate` |
| `hours_per_week` | `BIGINT` | Continuous | Self-reported typical weekly work hours | 1 - 99 hours |
| `capital_gain` | `BIGINT` | Continuous | Capital gains recorded on tax filings | \$0 - \$99,999 |
| `high_income` | `BIGINT` | Binary Label | Target indicator: whether income exceeds \$50,000 | `0` (<= \$50K), `1` (> \$50K) |

---

## 3. Analytical Considerations
1. **Class Imbalance:** Approximately 24% of records represent high-income earners (`high_income = 1`).
2. **Education Stratification:** Higher education levels (Bachelors, Masters, Doctorate) show positive correlation with the high-income threshold.
3. **Capital Gains Sparsity:** `capital_gain` is heavily right-skewed with high zero-inflation.
