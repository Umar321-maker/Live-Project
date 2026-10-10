"""
dashboard/app.py — Streamlit Retention Priority Dashboard
Run: streamlit run dashboard/app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from features import prepare_data

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "lgbm_best.pkl")
RETENTION_COST = 500

st.set_page_config(page_title="Churn Retention Dashboard", layout="wide")
st.title("📡 Telco Churn — Retention Priority Dashboard")

@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)

@st.cache_data
def load_scored_data():
    X, y = prepare_data()
    pipe = load_model()
    probs = pipe.predict_proba(X)[:, 1]
    df = X.copy()
    df["actual_churn"] = y.values
    df["churn_prob"] = probs
    df["risk_tier"] = pd.cut(probs, bins=[0, 0.35, 0.6, 1.0],
                              labels=["Low", "Medium", "High"])
    df["retention_priority_score"] = probs * df["clv"]
    return df.sort_values("retention_priority_score", ascending=False).reset_index(drop=True)

pipe = load_model()
df = load_scored_data()

# ── Sidebar filters ──────────────────────────────────────────────────────────
st.sidebar.header("Filters")
risk_filter = st.sidebar.multiselect("Risk Tier", ["High", "Medium", "Low"],
                                      default=["High", "Medium"])
top_n = st.sidebar.slider("Show top N customers", 10, 500, 100)

filtered = df[df["risk_tier"].isin(risk_filter)].head(top_n)

# ── KPI row ──────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Customers at Risk", len(filtered))
col2.metric("Avg Churn Probability", f"{filtered['churn_prob'].mean():.1%}")
col3.metric("Total CLV at Risk", f"₹{filtered['clv'].sum():,.0f}")
col4.metric("Retention Budget (est.)", f"₹{len(filtered) * RETENTION_COST:,.0f}")

st.divider()

# ── ROI comparison ────────────────────────────────────────────────────────────
st.subheader("ROI: Targeted vs Blanket Campaign")
avg_clv_churner = df[df["actual_churn"] == 1]["clv"].mean()
n_targeted = len(filtered)
tp_est = int(filtered["churn_prob"].sum())  # expected true positives

cost_targeted = n_targeted * RETENTION_COST
rev_targeted = tp_est * avg_clv_churner
roi_targeted = (rev_targeted - cost_targeted) / max(cost_targeted, 1)

cost_blanket = len(df) * RETENTION_COST
rev_blanket = int(df["actual_churn"].sum()) * avg_clv_churner
roi_blanket = (rev_blanket - cost_blanket) / max(cost_blanket, 1)

roi_df = pd.DataFrame({
    "Campaign": ["Targeted", "Blanket"],
    "Cost (₹)": [cost_targeted, cost_blanket],
    "Est. Revenue Saved (₹)": [rev_targeted, rev_blanket],
    "ROI": [roi_targeted, roi_blanket],
})
st.dataframe(roi_df.style.format({"Cost (₹)": "₹{:,.0f}",
                                   "Est. Revenue Saved (₹)": "₹{:,.0f}",
                                   "ROI": "{:.1%}"}), use_container_width=True)

st.divider()

# ── Risk distribution ─────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Churn Probability Distribution")
    fig = px.histogram(df, x="churn_prob", color="risk_tier",
                       nbins=40, barmode="overlay",
                       color_discrete_map={"High":"#e74c3c","Medium":"#f39c12","Low":"#2ecc71"})
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("Risk × CLV Scatter")
    fig2 = px.scatter(filtered.head(200), x="churn_prob", y="clv",
                      color="risk_tier", size="retention_priority_score",
                      hover_data=["MonthlyCharges", "tenure"],
                      color_discrete_map={"High":"#e74c3c","Medium":"#f39c12","Low":"#2ecc71"})
    st.plotly_chart(fig2, use_container_width=True)

# ── Priority table ────────────────────────────────────────────────────────────
st.subheader(f"Top {top_n} Customers by Retention Priority Score")
display_cols = ["churn_prob", "risk_tier", "clv", "retention_priority_score",
                "tenure", "MonthlyCharges", "Contract", "PaymentMethod"]
available = [c for c in display_cols if c in filtered.columns]
st.dataframe(
    filtered[available].style.format({
        "churn_prob": "{:.1%}",
        "clv": "₹{:,.0f}",
        "retention_priority_score": "₹{:,.0f}",
        "MonthlyCharges": "₹{:.0f}",
    }).background_gradient(subset=["churn_prob"], cmap="Reds"),
    use_container_width=True,
    height=400,
)

# ── Download ──────────────────────────────────────────────────────────────────
csv = filtered[available].to_csv(index=False)
st.download_button("⬇ Download Priority List (CSV)", csv,
                   "retention_priority_list.csv", "text/csv")
