# Data Quality Report
## Telco Customer Churn Dataset

**Date:** 2026-03-10  
**Source:** IBM Cognos Analytics sample dataset (CC BY-SA 4.0)  
**File:** WA_Fn-UseC_-Telco-Customer-Churn.csv (~955 KB)  
**Shape:** 7,043 rows × 21 columns  
**Data type:** Fictional/synthetic telco, California customers  

---

## 1. Critical Bug: TotalCharges Blank Strings

**Issue:** `TotalCharges` is stored as object dtype. Rows where `tenure == 0` have `TotalCharges = " "` (blank string), not `NaN`.  
**Count:** 11 affected rows  
**Fix:**
```python
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
df['TotalCharges'].fillna(0, inplace=True)
```

---

## 2. Class Imbalance

| Class | Count | % |
|-------|-------|---|
| No Churn (0) | 5,174 | 73.5% |
| Churn (1) | 1,869 | 26.5% |

**Mitigation:** `class_weight='balanced'` in sklearn models; SMOTE as alternative.

---

## 3. Pseudo-Category Collapse

Six service columns use a third value that is semantically identical to `"No"`:

| Column | Pseudo-value to collapse |
|--------|-------------------------|
| OnlineSecurity, OnlineBackup, DeviceProtection | `"No internet service"` |
| TechSupport, StreamingTV, StreamingMovies | `"No internet service"` |
| MultipleLines | `"No phone service"` |

**Fix:**
```python
no_internet = ['OnlineSecurity','OnlineBackup','DeviceProtection',
               'TechSupport','StreamingTV','StreamingMovies']
df[no_internet] = df[no_internet].replace('No internet service', 'No')
df['MultipleLines'] = df['MultipleLines'].replace('No phone service', 'No')
```

---

## 4. Descriptive Statistics (Key Numerics)

| Feature | Mean | Min | Max | Notes |
|---------|------|-----|-----|-------|
| tenure | 36.9 months | 1 | 72 | Right-skewed; bucket for modeling |
| MonthlyCharges | $69.85 | $18.25 | $118.75 | |
| TotalCharges | ~$2,283 | $0 | $8,684 | After blank-string fix |

---

## 5. Benchmark Churn Rates by Segment

| Segment | Churn Rate | Notes |
|---------|-----------|-------|
| Contract: Month-to-month | **35.5%** | Strongest single predictor |
| Contract: One year | ~11.3% | |
| Contract: Two year | **4.27%** | 8× lower than month-to-month |
| InternetService: Fiber optic | ~41.9% | Higher than DSL — counter-intuitive |
| InternetService: DSL | ~19.0% | |
| InternetService: No | ~7.4% | Lowest churn — discuss why |
| PaymentMethod: Electronic check | ~45.3% | Highest among payment methods |
| TechSupport: No | ~41.6% | vs. ~15% with support |
| OnlineSecurity: No | ~41.8% | vs. ~14.6% with security |

---

## 6. Key Hypotheses (from EDA)

| # | Hypothesis | Expected Direction |
|---|------------|--------------------|
| H1 | Month-to-month contract → higher churn | ✅ Confirmed |
| H2 | Low tenure (0–12 months) → higher churn | ✅ Confirmed |
| H3 | Electronic check payment → higher churn | ✅ Confirmed |
| H4 | No OnlineSecurity + No TechSupport → higher churn | ✅ Confirmed |
| H5 | Fiber optic internet → higher churn than DSL | ✅ Confirmed (41.9% vs 19.0%) |
| H6 | No-internet customers churn least | ✅ Counter-intuitive (7.4%) — discuss |
| H7 | Senior citizens churn more | Moderate signal |

---

## 7. Feature Summary

| Feature | Type | Notes |
|---------|------|-------|
| customerID | ID | Drop before modeling |
| gender | Binary cat | Low signal expected |
| SeniorCitizen | Binary int | Already 0/1 |
| Partner, Dependents | Binary cat | |
| tenure | Numeric | Key driver; bucket into 0-12, 13-24, 25-48, 49-72 |
| PhoneService, MultipleLines | Binary cat | |
| InternetService | 3-class cat | DSL / Fiber optic / No |
| OnlineSecurity … StreamingMovies | Binary cat | Collapse "No internet service" |
| Contract | 3-class cat | **Strongest driver** |
| PaperlessBilling | Binary cat | |
| PaymentMethod | 4-class cat | Electronic check is high-risk |
| MonthlyCharges | Numeric | |
| TotalCharges | Numeric | Fix blank strings |
| Churn | Target | Yes/No → 1/0 |
