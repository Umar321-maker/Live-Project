"""
src/features.py — Feature engineering pipeline for Telco Churn
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler

RAW_PATH = "data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv"
PROCESSED_PATH = "data/processed/telco_features.csv"

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


def load_and_clean(path: str = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Fix TotalCharges blank-string bug
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["TotalCharges"].fillna(0, inplace=True)

    # Collapse "No internet service" → "No"
    df[INTERNET_SERVICE_COLS] = df[INTERNET_SERVICE_COLS].replace(
        "No internet service", "No"
    )

    # Target encoding
    df["Churn"] = (df["Churn"] == "Yes").astype(int)

    # Drop ID
    df.drop(columns=["customerID"], inplace=True)

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
