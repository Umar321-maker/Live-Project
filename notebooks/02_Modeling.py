# %% [markdown]
# # Week 2–3 — Modeling, Tuning & Explainability

# %%
# Run from repo root: python notebooks/02_Modeling.py
import subprocess, sys
sys.path.insert(0, "src")

# %% [markdown]
# ## Step 1: Feature Engineering

# %%
from features import prepare_data
X, y = prepare_data()
print(f"X shape: {X.shape}  |  Churn rate: {y.mean():.1%}")

# %% [markdown]
# ## Step 2: Train All Models (Baseline + Tuned)

# %%
# This logs to MLflow and saves artifacts to models/
# View results: mlflow ui  →  http://localhost:5000
subprocess.run([sys.executable, "src/train.py"], check=True)

# %% [markdown]
# ## Step 3: SHAP + Error Analysis + ROI

# %%
subprocess.run([sys.executable, "src/evaluate.py"], check=True)

# %% [markdown]
# ## Step 4: View MLflow UI
# ```bash
# mlflow ui
# # Open http://localhost:5000
# ```
print("Done. Run `mlflow ui` to compare experiments.")
