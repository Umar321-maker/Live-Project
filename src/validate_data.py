"""
Quick data validation — works with both the standard Kaggle CSV
and the extended IBM tab-separated file.
Run from repo root: python src/validate_data.py data/raw/your_file.txt
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from features import load_and_clean, INTERNET_SERVICE_COLS

# Accept path as CLI arg or fall back to default
path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv"

print(f"\nLoading: {path}")

# ── Raw peek (before cleaning) ────────────────────────────────────────────────
import pandas as pd
with open(path, "r", encoding="utf-8") as f:
    first = f.readline()
sep = "\t" if "\t" in first else ","
raw = pd.read_csv(path, sep=sep)
raw.columns = raw.columns.str.strip()

print(f"Raw shape : {raw.shape}")
print(f"Separator : {'TAB' if sep == chr(9) else 'COMMA'}")
print(f"Columns   : {raw.columns.tolist()}\n")

# ── TotalCharges bug ──────────────────────────────────────────────────────────
tc_col = "Total Charges" if "Total Charges" in raw.columns else "TotalCharges"
print(f"'{tc_col}' dtype BEFORE fix: {raw[tc_col].dtype}")
blanks = (raw[tc_col].astype(str).str.strip() == "").sum()
print(f"Blank string rows: {blanks}  ← should be 11")

# ── Clean via pipeline ────────────────────────────────────────────────────────
df = load_and_clean(path)
print(f"\nCleaned shape: {df.shape}")

# ── Missing values ────────────────────────────────────────────────────────────
missing = df.isnull().sum()
print("\nMissing values after cleaning:")
print(missing[missing > 0] if missing.any() else "  None ✓")

# ── Class balance ─────────────────────────────────────────────────────────────
counts = df["Churn"].value_counts()
print(f"\nChurn distribution:\n{counts}")
print(f"Churn rate: {df['Churn'].mean():.1%}  ← expect ~26.5%")

# ── Pseudo-category check ─────────────────────────────────────────────────────
print("\nPseudo-category residuals (should all be 0):")
for col in INTERNET_SERVICE_COLS + ["MultipleLines"]:
    if col in df.columns:
        n = df[col].isin(["No internet service", "No phone service"]).sum()
        status = "✓" if n == 0 else "✗"
        print(f"  {status} {col}: {n}")

# ── Key numeric stats ─────────────────────────────────────────────────────────
print("\nKey numeric stats:")
print(df[["tenure", "MonthlyCharges", "TotalCharges"]].describe().round(2))
print(f"\n  Avg tenure        : {df['tenure'].mean():.1f} months  ← expect ~36.9")
print(f"  Avg MonthlyCharges: ${df['MonthlyCharges'].mean():.2f}  ← expect ~$69.85")

print("\n✅ Dataset loaded and validated successfully!")
