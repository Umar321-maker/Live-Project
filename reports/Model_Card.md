# Model Card — Telco Churn Classifier

## Model Details
- **Algorithm:** LightGBM (tuned via Optuna, 30 trials)
- **Training data:** 7,043 customers, 80/20 train-test split, stratified
- **Imbalance handling:** `class_weight='balanced'`
- **Threshold:** Cost-sensitive (tuned to maximize TP × avg_CLV − FP × ₹500)

## Performance (5-fold CV on train set)
| Metric | Score |
|--------|-------|
| ROC-AUC | ~0.85+ |
| F1 (churn class) | ~0.65+ |
| Precision@Top-Decile | ~0.60+ |

*(Exact values populated after training)*

## Top SHAP Drivers (expected)
1. Contract type (month-to-month)
2. Tenure
3. MonthlyCharges
4. TechSupport = No
5. OnlineSecurity = No

## Known Limitations
- CLV is a simplified proxy (MonthlyCharges × tenure); does not account for future revenue
- Model trained on a single static snapshot; no temporal validation
- High-tenure, high-CLV churners are the costliest false negatives — monitor this segment

## Intended Use
- Batch scoring of customer base quarterly
- Input to retention campaign prioritization
- NOT for automated adverse actions without human review

## Fairness Considerations
- `gender` and `SeniorCitizen` are included as features; monitor for disparate impact
- Recommend periodic fairness audits across demographic segments
