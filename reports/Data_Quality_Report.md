# Data Quality Report
## Telco Customer Churn Dataset

**Date:** 2026-03-10  
**Dataset:** WA_Fn-UseC_-Telco-Customer-Churn.csv  
**Shape:** 7,043 rows × 21 columns  

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
| No Churn (0) | 5,174 | 73.4% |
| Churn (1) | 1,869 | 26.6% |

**Mitigation:** `class_weight='balanced'` in sklearn models; SMOTE as alternative.

---

## 3. "No Internet Service" Pseudo-Categories

The following features use "No internet service" as a value, which is semantically identical to "No":

- `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`
- `TechSupport`, `StreamingTV`, `StreamingMovies`

**Fix:** Collapse to binary Yes/No.
```python
cols = ['OnlineSecurity','OnlineBackup','DeviceProtection',
        'TechSupport','StreamingTV','StreamingMovies']
df[cols] = df[cols].replace('No internet service', 'No')
```

---

## 4. Key Hypotheses (from EDA)

| # | Hypothesis | Expected Direction |
|---|------------|--------------------|
| H1 | Month-to-month contract → higher churn | ✅ Confirmed |
| H2 | Low tenure (0–12 months) → higher churn | ✅ Confirmed |
| H3 | Electronic check payment → higher churn | ✅ Confirmed |
| H4 | No OnlineSecurity + No TechSupport → higher churn | ✅ Confirmed |
| H5 | Fiber optic internet → higher churn than DSL | ✅ Confirmed |
| H6 | Senior citizens churn more | Moderate signal |

---

## 5. Feature Summary

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
