"""
api/main.py — FastAPI /predict endpoint
POST /predict  →  { churn_probability, risk_tier, top_3_drivers, clv }
"""
import joblib
import shap
import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from features import engineer_features, load_and_clean, NUMERIC, BINARY_CATS, MULTI_CATS

app = FastAPI(title="Telco Churn Predictor", version="1.0")

# Load model once at startup
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "lgbm_best.pkl")
pipe = joblib.load(MODEL_PATH)
explainer = shap.TreeExplainer(pipe.named_steps["clf"])


class CustomerProfile(BaseModel):
    gender: str
    SeniorCitizen: int
    Partner: str
    Dependents: str
    tenure: int
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str
    MonthlyCharges: float
    TotalCharges: float


def get_feature_names() -> list:
    pre = pipe.named_steps["pre"]
    bin_names = pre.named_transformers_["bin"].get_feature_names_out(
        BINARY_CATS + ["tenure_bucket"]
    ).tolist()
    cat_names = pre.named_transformers_["cat"].get_feature_names_out(MULTI_CATS).tolist()
    return NUMERIC + bin_names + cat_names


@app.post("/predict")
def predict(customer: CustomerProfile):
    df = pd.DataFrame([customer.model_dump()])

    # Replicate cleaning
    internet_cols = ["OnlineSecurity","OnlineBackup","DeviceProtection",
                     "TechSupport","StreamingTV","StreamingMovies"]
    df[internet_cols] = df[internet_cols].replace("No internet service", "No")

    # Engineer features
    df["clv"] = df["MonthlyCharges"] * df["tenure"]
    df["avg_monthly_spend"] = np.where(
        df["tenure"] > 0, df["TotalCharges"] / df["tenure"], df["MonthlyCharges"]
    )
    service_cols = internet_cols + ["PhoneService", "MultipleLines"]
    df["services_count"] = (df[service_cols] == "Yes").sum(axis=1)
    df["tenure_bucket"] = pd.cut(
        df["tenure"], bins=[0,12,24,48,72],
        labels=["0-12","13-24","25-48","49-72"], include_lowest=True
    )

    prob = float(pipe.predict_proba(df)[:, 1][0])
    risk_tier = "High" if prob >= 0.6 else "Medium" if prob >= 0.35 else "Low"

    # SHAP top-3 drivers
    X_t = pipe.named_steps["pre"].transform(df)
    sv = explainer.shap_values(X_t)
    sv_row = sv[1][0] if isinstance(sv, list) else sv[0]
    feat_names = get_feature_names()
    top3_idx = np.argsort(np.abs(sv_row))[::-1][:3]
    top3 = [{"feature": feat_names[i], "shap_value": round(float(sv_row[i]), 4)}
            for i in top3_idx]

    return {
        "churn_probability": round(prob, 4),
        "risk_tier": risk_tier,
        "clv": round(float(df["clv"].iloc[0]), 2),
        "top_3_drivers": top3,
    }


@app.get("/health")
def health():
    return {"status": "ok"}
