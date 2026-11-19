# Titanic Passenger Survival Data Dictionary

## 1. Overview
The Titanic dataset records passenger demographics, ticketing, and survival statuses from the RMS Titanic.
In Athena, it is used as a standard benchmark for testing demographic subgroup analysis, causal
reasoning boundaries on historical observational records, and logistic survival classification.

- **Dataset ID:** `titanic`
- **Primary Target:** `survived` (binary classification: 1 = survived, 0 = deceased)
- **Granularity:** One record per onboard passenger

---

## 2. Feature Schema & Column Definitions

| Column Name | Physical Type | Semantic Type | Description | Values / Range |
| :--- | :--- | :--- | :--- | :--- |
| `passenger_id` | `BIGINT` | Identifier | Sequential unique passenger record number | 1 - 891 |
| `survived` | `BIGINT` | Binary Label | Target outcome: whether passenger survived disaster | `0` (Deceased), `1` (Survived) |
| `pclass` | `BIGINT` | Ordinal | Ticket travel cabin class | `1` (1st), `2` (2nd), `3` (3rd) |
| `sex` | `VARCHAR` | Categorical | Biological sex of the passenger | `male`, `female` |
| `age` | `DOUBLE` | Continuous | Age of passenger in years (fractional if < 1) | 0.42 - 80.0 |
| `sibsp` | `BIGINT` | Count | Number of siblings and spouses traveling aboard | 0 - 8 |
| `parch` | `BIGINT` | Count | Number of parents and children traveling aboard | 0 - 6 |
| `fare` | `DOUBLE` | Continuous | Passenger ticket fare paid in British Pounds (GBP) | £0.00 - £512.33 |
| `embarked` | `VARCHAR` | Categorical | Port of embarkation | `C` (Cherbourg), `Q` (Queenstown), `S` (Southampton) |

---

## 3. Analytical Considerations
1. **Gender Survival Disparity:** Female survival rate (~74.2%) dramatically exceeded male survival rate (~18.9%).
2. **Socio-Economic Class Effect:** 1st class passengers survived at a significantly higher rate (~63%) than 3rd class (~24%).
3. **Age Missingness:** Age contains approximately 19.9% null values, requiring explicit imputation or caveat handling.
