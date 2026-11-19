# California Housing Data Dictionary

## 1. Overview
The California Housing dataset contains aggregated census block group metrics from the 1990 U.S. Census.
It is utilized in Athena for continuous regression benchmarks, geographic geospatial clustering, and
macroeconomic price prediction.

- **Dataset ID:** `california_housing`
- **Primary Target:** `medhouseval` (continuous regression: median home value in \$100,000s)
- **Granularity:** One record per census block group (typically 600 to 3,000 individuals)

---

## 2. Feature Schema & Column Definitions

| Column Name | Physical Type | Semantic Type | Description | Values / Range |
| :--- | :--- | :--- | :--- | :--- |
| `medinc` | `DOUBLE` | Continuous | Median income of block group residents (\$10,000s) | 0.4999 - 15.0001 |
| `houseage` | `DOUBLE` | Continuous | Median age of residential structures in the block group | 1.0 - 52.0 years |
| `averooms` | `DOUBLE` | Continuous | Average total rooms per household in block group | 0.846 - 141.909 |
| `avebedrms` | `DOUBLE` | Continuous | Average bedrooms per household in block group | 0.333 - 34.066 |
| `population` | `DOUBLE` | Continuous | Total resident population residing in block group | 3.0 - 35,682.0 |
| `aveoccup` | `DOUBLE` | Continuous | Average number of household members per unit | 0.692 - 1243.333 |
| `latitude` | `DOUBLE` | Geographic | Block group centroid latitude coordinate | 32.54 - 41.95 degrees N |
| `longitude` | `DOUBLE` | Geographic | Block group centroid longitude coordinate | -124.35 to -114.31 degrees W |
| `medhouseval` | `DOUBLE` | Continuous Label | Median house value for households within block (\$100K) | 0.14999 - 5.00001 |

---

## 3. Analytical Considerations
1. **Target Truncation:** `medhouseval` is capped at \$5.00001 (\$500,000), resulting in an artificial spike at the ceiling.
2. **Median Income Dominance:** `medinc` is the single strongest linear predictor of `medhouseval` (Pearson r ~ 0.69).
3. **Geographic Nonlinearity:** Coastal proximity (latitude / longitude) introduces non-linear spatial price adjustments.
