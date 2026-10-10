# Business Requirements Document (BRD)
## Telco Customer Churn Prediction

**Version:** 1.1  
**Date:** 2026-03-10  
**Stakeholder:** CFO, Regional Telecom  
**Dataset:** WA_Fn-UseC_-Telco-Customer-Churn.csv (IBM Cognos Analytics sample, CC BY-SA 4.0)  

---

## 1. Business Problem

Customer churn directly erodes revenue. Acquiring a new customer costs 5–7× more than retaining an existing one. The CFO needs to answer three questions:
1. Which customers will churn next quarter?
2. Why are they churning?
3. What is the ROI of a targeted retention campaign vs. a blanket discount?

---

## 2. Business Objective

Build a binary churn classifier that outputs:
- Churn probability per customer
- Top 3 drivers of that customer's churn risk (SHAP)
- A ranked retention priority list weighted by **CLV**

---

## 3. Customer Lifetime Value (CLV) Definition

```
CLV = MonthlyCharges × tenure   (in months)
```

This is a simplified CLV proxy. A customer with MonthlyCharges = ₹5,000 and tenure = 24 months has CLV = ₹1,20,000.

**Business implication:** A false negative (missed churner) on a high-CLV customer is far more costly than on a low-CLV customer. This drives cost-sensitive threshold tuning in Week 3.

---

## 4. Success Metrics

| Metric | Target |
|--------|--------|
| ROC-AUC | ≥ 0.85 |
| F1-Score (churn class) | ≥ 0.65 |
| Precision@Top-Decile | ≥ 0.60 |
| Business: Revenue saved vs. blanket discount | Quantified in ₹ |

---

## 5. Retention Campaign ROI Framework

**Blanket discount:** Apply a 20% discount to all 7,043 customers.  
**Targeted campaign:** Apply discount only to top-decile risk customers (~704 customers).

```
Cost_blanket     = 7043 × discount_amount
Cost_targeted    = 704  × discount_amount
Revenue_saved    = (True Positives in top decile) × avg_CLV_of_churners
ROI_targeted     = (Revenue_saved - Cost_targeted) / Cost_targeted
ROI_blanket      = (Revenue_saved_blanket - Cost_blanket) / Cost_blanket
```

The model's value is demonstrated when `ROI_targeted > ROI_blanket`.

---

## 6. Data Source

- **Dataset:** Telco Customer Churn — IBM Cognos Analytics sample (via Kaggle: blastchar/telco-customer-churn)
- **License:** CC BY-SA 4.0
- **Size:** 7,043 rows × 21 columns (~955 KB CSV)
- **Geography:** Fictional telco, customers in California
- **Target:** `Churn` (Yes/No → 1/0)
- **Class balance:** 26.5% churn (1,869 churners / 5,174 retained)

### Column Groups
| Group | Columns |
|-------|---------|
| Identifier | customerID |
| Demographics | gender, SeniorCitizen, Partner, Dependents |
| Account | tenure, Contract, PaperlessBilling, PaymentMethod, MonthlyCharges, TotalCharges |
| Services | PhoneService, MultipleLines, InternetService, OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport, StreamingTV, StreamingMovies |
| Target | Churn |

### Known Data Quirks
- `TotalCharges` stored as object dtype — 11 blank-string rows (tenure=0) require `pd.to_numeric(errors='coerce')`
- Six service columns use `"No internet service"` / `"No phone service"` as a pseudo-category — collapse to `"No"` before modeling
- No true missing values otherwise (unusually clean for production data)

### Known Benchmark Findings
- Month-to-month contracts: **35.5% churn rate** — 8× higher than two-year contracts (4.27%); `Contract` is the single strongest predictor
- Average tenure: **36.9 months** (range 1–72); average monthly charges: **$69.85**
- Fiber optic customers churn more than DSL; no-internet customers churn least — counter-intuitive, worth discussing
- Electronic check payment + absence of TechSupport/OnlineSecurity are consistently top SHAP drivers

---

## 7. Constraints & Assumptions

- No real-time data pipeline; batch scoring is sufficient
- Retention offer cost assumed at ₹500/customer for ROI calculation
- Model must be explainable (SHAP) — black-box alone is not acceptable to CFO
- Deployment target: Docker container on internal server + Streamlit dashboard

---

## 8. Out of Scope

- Real-time streaming churn detection
- Customer segmentation / clustering
- Pricing optimization
