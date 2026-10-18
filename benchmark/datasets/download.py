"""Dataset downloader and generator for Athena benchmarks."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import fetch_california_housing


def generate_california_housing(dest: Path) -> Path:
    """Fetch or generate California Housing dataset."""
    data = fetch_california_housing(as_frame=True)
    df = data.frame.copy()
    df.columns = [c.lower() for c in df.columns]
    out_file = dest / "california_housing.csv"
    df.to_csv(out_file, index=False)
    return out_file


def generate_california_housing_leakage(dest: Path, base_path: Path) -> Path:
    """Planted leakage: luxury property tax is directly derived from medhouseval."""
    df = pd.read_csv(base_path)
    df["luxury_property_tax"] = np.where(df["medhouseval"] > 3.0, 15000.0, 2000.0)
    out_file = dest / "california_housing_leakage.csv"
    df.to_csv(out_file, index=False)
    return out_file


def generate_telco_churn(dest: Path, n_rows: int = 1000) -> Path:
    """Generate realistic synthetic Telco Churn dataset."""
    np.random.seed(42)
    customer_ids = [f"CUST_{i:05d}" for i in range(1, n_rows + 1)]
    tenure = np.random.randint(1, 72, size=n_rows)
    contracts = np.random.choice(
        ["Month-to-month", "One year", "Two year"],
        size=n_rows,
        p=[0.55, 0.25, 0.20],
    )
    paperless = np.random.choice(["Yes", "No"], size=n_rows, p=[0.6, 0.4])
    payment = np.random.choice(
        ["Electronic check", "Mailed check", "Bank transfer", "Credit card"],
        size=n_rows,
    )
    monthly_charges = np.round(np.random.uniform(20.0, 118.0, size=n_rows), 2)
    total_charges = np.round(
        tenure * monthly_charges + np.random.normal(0, 10, size=n_rows),
        2,
    )
    total_charges = np.maximum(total_charges, monthly_charges)

    logits = (
        -1.5
        + (contracts == "Month-to-month") * 1.2
        + (monthly_charges > 70) * 0.8
        - (tenure > 30) * 0.9
    )
    probs = 1.0 / (1.0 + np.exp(-logits))
    churn = (np.random.rand(n_rows) < probs).astype(int)

    df = pd.DataFrame({
        "customer_id": customer_ids,
        "tenure": tenure,
        "contract": contracts,
        "paperless_billing": paperless,
        "payment_method": payment,
        "monthly_charges": monthly_charges,
        "total_charges": total_charges,
        "churn": churn,
    })

    out_file = dest / "telco_churn.csv"
    df.to_csv(out_file, index=False)
    return out_file


def generate_telco_churn_leakage(dest: Path, base_churn_path: Path) -> Path:
    """Generate planted-leakage variant with a direct future leak column."""
    df = pd.read_csv(base_churn_path)
    df["cancellation_fee"] = np.where(df["churn"] == 1, 99.00, 0.00)
    out_file = dest / "telco_churn_leakage.csv"
    df.to_csv(out_file, index=False)
    return out_file


def generate_adult_income(dest: Path, n_rows: int = 1000) -> Path:
    """Generate realistic synthetic Adult Income dataset."""
    np.random.seed(42)
    age = np.random.randint(18, 75, size=n_rows)
    education = np.random.choice(
        ["Bachelors", "HS-grad", "11th", "Masters", "9th", "Some-college", "Doctorate"],
        size=n_rows,
        p=[0.25, 0.32, 0.05, 0.12, 0.04, 0.18, 0.04],
    )
    hours_per_week = np.random.choice([20, 40, 50, 60], size=n_rows, p=[0.1, 0.6, 0.2, 0.1])
    workclass = np.random.choice(["Private", "Self-emp", "Gov", "State-gov"], size=n_rows)
    capital_gain = np.random.choice(
        [0, 5000, 10000, 20000],
        size=n_rows,
        p=[0.85, 0.08, 0.05, 0.02],
    )

    higher_ed = np.isin(education, ["Bachelors", "Masters", "Doctorate"])
    logits = (
        -2.0
        + (age > 35) * 0.8
        + higher_ed * 1.5
        + (hours_per_week > 40) * 0.5
    )
    high_income = (np.random.rand(n_rows) < (1.0 / (1.0 + np.exp(-logits)))).astype(int)

    df = pd.DataFrame({
        "age": age,
        "workclass": workclass,
        "education": education,
        "hours_per_week": hours_per_week,
        "capital_gain": capital_gain,
        "high_income": high_income,
    })

    out_file = dest / "adult_income.csv"
    df.to_csv(out_file, index=False)
    return out_file


def generate_adult_income_leakage(dest: Path, base_path: Path) -> Path:
    """Planted leakage: tax bracket fee only paid by high income earners."""
    df = pd.read_csv(base_path)
    df["tax_bracket_50k_fee"] = np.where(df["high_income"] == 1, 12500.0, 0.0)
    out_file = dest / "adult_income_leakage.csv"
    df.to_csv(out_file, index=False)
    return out_file


def generate_titanic(dest: Path, n_rows: int = 891) -> Path:
    """Generate synthetic Titanic survival benchmark dataset."""
    np.random.seed(42)
    pclass = np.random.choice([1, 2, 3], size=n_rows, p=[0.24, 0.21, 0.55])
    sex = np.random.choice(["female", "male"], size=n_rows, p=[0.35, 0.65])
    age = np.round(np.random.normal(29.7, 14.5, size=n_rows), 1)
    age = np.clip(age, 1.0, 80.0)
    sibsp = np.random.choice([0, 1, 2, 3], size=n_rows, p=[0.68, 0.23, 0.06, 0.03])
    parch = np.random.choice([0, 1, 2], size=n_rows, p=[0.76, 0.16, 0.08])
    fare = np.where(
        pclass == 1,
        np.random.exponential(60.0, size=n_rows) + 30.0,
        np.where(
            pclass == 2,
            np.random.exponential(15.0, size=n_rows) + 10.0,
            np.random.exponential(8.0, size=n_rows) + 4.0,
        ),
    )
    fare = np.round(fare, 2)
    embarked = np.random.choice(["S", "C", "Q"], size=n_rows, p=[0.72, 0.19, 0.09])

    logits = (
        -1.2
        + (sex == "female") * 2.5
        + (pclass == 1) * 1.3
        + (pclass == 2) * 0.5
        - (age > 50) * 0.4
    )
    probs = 1.0 / (1.0 + np.exp(-logits))
    survived = (np.random.rand(n_rows) < probs).astype(int)

    df = pd.DataFrame({
        "passenger_id": list(range(1, n_rows + 1)),
        "survived": survived,
        "pclass": pclass,
        "sex": sex,
        "age": age,
        "sibsp": sibsp,
        "parch": parch,
        "fare": fare,
        "embarked": embarked,
    })

    out_file = dest / "titanic.csv"
    df.to_csv(out_file, index=False)
    return out_file


def download_all_datasets(target_dir: Path | None = None) -> dict[str, Path]:
    """Download and generate all benchmark datasets."""
    dest = target_dir or (Path(__file__).parent)
    dest.mkdir(parents=True, exist_ok=True)

    churn = generate_telco_churn(dest)
    churn_leak = generate_telco_churn_leakage(dest, churn)
    housing = generate_california_housing(dest)
    housing_leak = generate_california_housing_leakage(dest, housing)
    income = generate_adult_income(dest)
    income_leak = generate_adult_income_leakage(dest, income)
    titanic = generate_titanic(dest)

    return {
        "telco_churn": churn,
        "telco_churn_leakage": churn_leak,
        "california_housing": housing,
        "california_housing_leakage": housing_leak,
        "adult_income": income,
        "adult_income_leakage": income_leak,
        "titanic": titanic,
    }


if __name__ == "__main__":
    download_all_datasets()
