# Telco Customer Churn Data Dictionary

## 1. Overview
The Telco Customer Churn dataset simulates customer behavior across telecommunications services.
It is primarily utilized within the Athena Benchmark suite to evaluate customer attrition analysis,
contract cohort segmentation, and predictive churn modeling.

- **Dataset ID:** `telco_churn`
- **Primary Target:** `churn` (binary classification: 1 = churned, 0 = retained)
- **Granularity:** One record per customer account

---

## 2. Feature Schema & Column Definitions

| Column Name | Physical Type | Semantic Type | Description | Values / Range |
| :--- | :--- | :--- | :--- | :--- |
| `customer_id` | `VARCHAR` | Identifier | Unique account identifier | Alphanumeric (e.g. `7590-VHVEG`) |
| `tenure` | `BIGINT` | Continuous | Number of months the customer has been with the provider | 0 - 72 months |
| `contract` | `VARCHAR` | Categorical | Contract agreement commitment term | `Month-to-month`, `One year`, `Two year` |
| `paperless_billing` | `VARCHAR` | Binary | Customer opted into digital paperless invoicing | `Yes`, `No` |
| `payment_method` | `VARCHAR` | Categorical | Billing payment method on file | `Electronic check`, `Mailed check`, `Bank transfer`, `Credit card` |
| `monthly_charges` | `DOUBLE` | Continuous | Recurring fee charged to customer monthly (USD) | \$18.25 - \$118.75 |
| `total_charges` | `DOUBLE` | Continuous | Cumulative expenditure across account lifetime | \$18.80 - \$8684.80 |
| `churn` | `BIGINT` | Binary Label | Target label: whether customer terminated service | `0` (Retained), `1` (Churned) |

---

## 3. Analytical Considerations
1. **Tenure Inversion:** Churn rate is inversely related to tenure; customers in their first 6 months exhibit peak churn probability.
2. **Contract Segmentation:** Month-to-month accounts experience significantly higher churn rates (>40%) than annual contracts (<12%).
3. **Missing Value Handling:** Total charges may contain nulls or whitespace for brand-new customers with 0 tenure.
