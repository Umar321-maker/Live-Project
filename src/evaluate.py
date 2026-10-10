"""
src/evaluate.py — SHAP analysis, cost-sensitive threshold tuning, error analysis
Run: python src/evaluate.py
"""
import joblib
import shap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    classification_report, roc_auc_score,
    precision_recall_curve, confusion_matrix,
)
from sklearn.model_selection import train_test_split
from features import prepare_data, build_preprocessor, NUMERIC, BINARY_CATS, MULTI_CATS

MODEL_PATH = "models/lgbm_best.pkl"   # swap to xgb_best.pkl if preferred
RETENTION_COST = 500    # ₹ per customer contacted
AVG_CLV_CHURNER = None  # computed from data


def get_feature_names(pipe) -> list:
    pre = pipe.named_steps["pre"]
    num_names = NUMERIC
    bin_names = pre.named_transformers_["bin"].get_feature_names_out(
        BINARY_CATS + ["tenure_bucket"]
    ).tolist()
    cat_names = pre.named_transformers_["cat"].get_feature_names_out(MULTI_CATS).tolist()
    return num_names + bin_names + cat_names


def shap_analysis(pipe, X_test, y_test):
    pre = pipe.named_steps["pre"]
    clf = pipe.named_steps["clf"]
    X_transformed = pre.transform(X_test)
    feature_names = get_feature_names(pipe)

    explainer = shap.TreeExplainer(clf)
    shap_values = explainer.shap_values(X_transformed)

    # For binary classifiers that return list, take class-1 values
    sv = shap_values[1] if isinstance(shap_values, list) else shap_values

    plt.figure()
    shap.summary_plot(sv, X_transformed, feature_names=feature_names, show=False)
    plt.tight_layout()
    plt.savefig("shap_outputs/shap_summary.png", dpi=150)
    plt.close()
    print("SHAP summary plot saved → shap_outputs/shap_summary.png")

    # Top 10 global drivers
    mean_abs = np.abs(sv).mean(axis=0)
    top10 = pd.Series(mean_abs, index=feature_names).nlargest(10)
    print("\nTop 10 SHAP drivers:\n", top10.to_string())
    return explainer, feature_names


def cost_sensitive_threshold(pipe, X_test, y_test, clv_series):
    probs = pipe.predict_proba(X_test)[:, 1]
    precision, recall, thresholds = precision_recall_curve(y_test, probs)

    # Expected value per threshold: TP × avg_CLV - FP × RETENTION_COST
    avg_clv = clv_series.mean()
    best_thresh, best_ev = 0.5, -np.inf
    for t in thresholds:
        preds = (probs >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, preds).ravel()
        ev = tp * avg_clv - fp * RETENTION_COST
        if ev > best_ev:
            best_ev, best_thresh = ev, t

    print(f"\nCost-sensitive threshold: {best_thresh:.3f}  (Expected value: ₹{best_ev:,.0f})")
    return best_thresh


def error_analysis(pipe, X_test, y_test, threshold=0.5):
    probs = pipe.predict_proba(X_test)[:, 1]
    preds = (probs >= threshold).astype(int)

    X_test = X_test.copy()
    X_test["actual"] = y_test.values
    X_test["predicted"] = preds
    X_test["prob"] = probs

    # False negatives — missed churners
    fn_df = X_test[(X_test["actual"] == 1) & (X_test["predicted"] == 0)]
    print(f"\nFalse Negatives: {len(fn_df)}")
    print("High-CLV missed churners (CLV > 75th pct):")
    clv_thresh = X_test["clv"].quantile(0.75)
    costly_fn = fn_df[fn_df["clv"] > clv_thresh]
    print(f"  Count: {len(costly_fn)}  |  Avg CLV: ₹{costly_fn['clv'].mean():,.0f}")
    print(classification_report(y_test, preds, target_names=["No Churn", "Churn"]))


def roi_analysis(pipe, X_test, y_test):
    probs = pipe.predict_proba(X_test)[:, 1]
    clv = X_test["clv"]
    avg_clv = clv[y_test == 1].mean()

    # Top decile targeted
    n_top = max(1, int(len(probs) * 0.10))
    top_idx = np.argsort(probs)[::-1][:n_top]
    tp_targeted = y_test.iloc[top_idx].sum()

    cost_targeted = n_top * RETENTION_COST
    revenue_targeted = tp_targeted * avg_clv
    roi_targeted = (revenue_targeted - cost_targeted) / cost_targeted

    # Blanket
    total_churners = y_test.sum()
    cost_blanket = len(y_test) * RETENTION_COST
    revenue_blanket = total_churners * avg_clv
    roi_blanket = (revenue_blanket - cost_blanket) / cost_blanket

    print(f"\n{'='*50}")
    print(f"ROI Analysis (avg CLV of churners = ₹{avg_clv:,.0f})")
    print(f"{'='*50}")
    print(f"Targeted (top 10%): Cost=₹{cost_targeted:,.0f}  Revenue=₹{revenue_targeted:,.0f}  ROI={roi_targeted:.1%}")
    print(f"Blanket:            Cost=₹{cost_blanket:,.0f}  Revenue=₹{revenue_blanket:,.0f}  ROI={roi_blanket:.1%}")
    print(f"Savings vs blanket: ₹{cost_blanket - cost_targeted:,.0f}")


if __name__ == "__main__":
    X, y = prepare_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    pipe = joblib.load(MODEL_PATH)

    shap_analysis(pipe, X_test, y_test)
    threshold = cost_sensitive_threshold(pipe, X_test, y_test, X_test["clv"])
    error_analysis(pipe, X_test, y_test, threshold)
    roi_analysis(pipe, X_test, y_test)
