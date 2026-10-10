# Live-project | Telco Customer Churn — DS Project

> **Business Question:** Which customers will churn next quarter, why, and what is the ROI of targeted retention vs. blanket discounts?

## Project Structure
```
├── data/
│   ├── raw/                  # WA_Fn-UseC_-Telco-Customer-Churn.csv
│   └── processed/            # cleaned + feature-engineered CSVs
├── notebooks/
│   ├── 01_EDA.ipynb
│   └── 02_Modeling.ipynb
├── src/
│   ├── features.py           # feature engineering pipeline
│   ├── train.py              # model training + MLflow logging
│   └── evaluate.py           # SHAP + threshold tuning + error analysis
├── api/
│   └── main.py               # FastAPI /predict endpoint
├── dashboard/
│   └── app.py                # Streamlit retention priority dashboard
├── models/                   # serialized model artifacts
├── reports/
│   ├── BRD.md
│   └── Data_Quality_Report.md
├── shap_outputs/             # SHAP plots
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Quickstart
```bash
pip install -r requirements.txt

# 1. Place raw CSV in data/raw/
# 2. Run EDA notebook
# 3. Train model
python src/train.py

# 4. Start API
uvicorn api.main:app --reload

# 5. Start dashboard
streamlit run dashboard/app.py
```

## Week-by-Week Deliverables
| Week | Deliverable |
|------|-------------|
| 1 | BRD, EDA notebook, Data Quality Report |
| 2 | features.py, baseline model (LR), F1/ROC-AUC benchmark |
| 3 | MLflow experiment log, best model, SHAP report, Model Card |
| 4 | FastAPI + Docker + Streamlit dashboard |
| 5 | Slide deck, demo video, final repo |
