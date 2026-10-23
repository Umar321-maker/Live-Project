"""
src/features.py — Feature engineering pipeline for Telco Churn

Supports two dataset variants:
  A) Standard Kaggle CSV  (WA_Fn-UseC_-Telco-Customer-Churn.csv)
     - comma-separated, camelCase columns, target = "Churn" (Yes/No)
  B) Extended IBM CSV / TSV  (spaces in column names, extra cols like
     "Churn Label", "CLTV", "Churn Reason", "Churn Score")
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler

RAW_PATH = "data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv"
PROCESSED_PATH = "data/processed/telco_features.csv"

# ── Column name maps: extended IBM names → standard names ────────────────────
_RENAME = {
    "CustomerID":        "customerID",
    "Gender":            "gender",
    "Senior Citizen":    "SeniorCitizen",
    "Tenure Months":     "tenure",
    "Phone Service":     "PhoneService",
    "Multiple Lines":    "MultipleLines",
    "Internet Service":  "InternetService",
    "Online Security":   "OnlineSecurity",
    "Online Backup":     "OnlineBackup",
    "Device Protection": "DeviceProtection",
    "Tech Support":      "TechSupport",
    "Streaming TV":      "StreamingTV",
    "Streaming Movies":  "StreamingMovies",
    "Paperless Billing": "PaperlessBilling",
    "Payment Method":    "PaymentMethod",
    "Monthly Charges":   "MonthlyCharges",
    "Total Charges":     "TotalCharges",
    "Churn Label":       "Churn",      # extended variant uses "Churn Label"
    "Churn Value":       "ChurnValue",
    "Churn Score":       "ChurnScore",
    "Churn Reason":      "ChurnReason",
    "Lat Long":          "LatLong",
    "Zip Code":          "ZipCode",
}

# Columns to drop before modelling (IDs, leakage, geo noise)
_DROP = [
    "customerID", "CustomerID",
    "Count", "Country", "State", "City", "ZipCode", "Zip Code",
    "Latitude", "Longitude", "LatLong", "Lat Long",
    "ChurnValue", "ChurnScore", "ChurnReason",   # leakage / post-hoc
    "CLTV",                                       # IBM's own CLV — we compute ours
]

INTERNET_SERVICE_COLS = [
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies",
]

BINARY_CATS = [
    "gender", "Partner", "Dependents", "PhoneService",
    "PaperlessBilling", "MultipleLines",
] + INTERNET_SERVICE_COLS

MULTI_CATS = ["InternetService", "Contract", "PaymentMethod"]

NUMERIC = ["tenure", "MonthlyCharges", "TotalCharges",
           "avg_monthly_spend", "services_count", "clv"]


def _detect_and_load(path: str) -> pd.DataFrame:
    """Auto-detect separator (tab vs comma) and load."""
    with open(path, "r", encoding="utf-8") as f:
        first_line = f.readline()
    sep = "\t" if "\t" in first_line else ","
    return pd.read_csv(path, sep=sep)


def load_and_clean(path: str = RAW_PATH) -> pd.DataFrame:
    df = _detect_and_load(path)

    # Normalise column names (strip whitespace)
    df.columns = df.columns.str.strip()

    # Rename extended IBM columns → standard names
    df.rename(columns=_RENAME, inplace=True)

    # If "Churn" still missing but "Churn Label" was renamed above, it's fine.
    # Fallback: use ChurnValue if present
    if "Churn" not in df.columns and "ChurnValue" in df.columns:
        df["Churn"] = df["ChurnValue"]

    # Drop leakage / geo / ID columns (ignore missing)
    df.drop(columns=[c for c in _DROP if c in df.columns], inplace=True)

    # Fix TotalCharges blank-string bug (11 rows where tenure == 0)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["TotalCharges"].fillna(0, inplace=True)

    # Collapse pseudo-categories → "No"
    df[INTERNET_SERVICE_COLS] = df[INTERNET_SERVICE_COLS].replace(
        "No internet service", "No"
    )
    df["MultipleLines"] = df["MultipleLines"].replace("No phone service", "No")

    # Normalise SeniorCitizen: "Yes"/"No" → 1/0 if needed
    if df["SeniorCitizen"].dtype == object:
        df["SeniorCitizen"] = (df["SeniorCitizen"] == "Yes").astype(int)

    # Target: Yes/No → 1/0  (already int if loaded from ChurnValue)
    if df["Churn"].dtype == object:
        df["Churn"] = (df["Churn"] == "Yes").astype(int)
    else:
        df["Churn"] = df["Churn"].astype(int)

    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    # CLV proxy
    df["clv"] = df["MonthlyCharges"] * df["tenure"]

    # Avg monthly spend (handles tenure=0)
    df["avg_monthly_spend"] = np.where(
        df["tenure"] > 0, df["TotalCharges"] / df["tenure"], df["MonthlyCharges"]
    )

    # Count of add-on services subscribed
    service_cols = INTERNET_SERVICE_COLS + ["PhoneService", "MultipleLines"]
    df["services_count"] = (df[service_cols] == "Yes").sum(axis=1)

    # Tenure bucket
    df["tenure_bucket"] = pd.cut(
        df["tenure"],
        bins=[0, 12, 24, 48, 72],
        labels=["0-12", "13-24", "25-48", "49-72"],
        include_lowest=True,
    )

    return df


def build_preprocessor() -> ColumnTransformer:
    binary_enc = OneHotEncoder(drop="if_binary", sparse_output=False, handle_unknown="ignore")
    multi_enc = OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore")
    scaler = StandardScaler()

    return ColumnTransformer(
        transformers=[
            ("num", scaler, NUMERIC),
            ("bin", binary_enc, BINARY_CATS + ["tenure_bucket"]),
            ("cat", multi_enc, MULTI_CATS),
        ],
        remainder="drop",
    )


def prepare_data(path: str = RAW_PATH):
    df = load_and_clean(path)
    df = engineer_features(df)
    df.to_csv(PROCESSED_PATH, index=False)
    print(f"Saved processed data → {PROCESSED_PATH}  shape={df.shape}")

    X = df.drop(columns=["Churn"])
    y = df["Churn"]
    return X, y


if __name__ == "__main__":
    prepare_data()
