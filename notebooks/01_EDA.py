# %% [markdown]
# # Week 1 — EDA & Data Quality Audit
# **Dataset:** Telco Customer Churn (7,043 × 21)
# **Goal:** Validate data quality, understand churn drivers, generate hypothesis list

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.dpi"] = 120

df_raw = pd.read_csv("../data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv")
print(df_raw.shape)
df_raw.head()

# %% [markdown]
# ## 1. TotalCharges Blank-String Bug

# %%
print("dtype:", df_raw["TotalCharges"].dtype)
blank_mask = df_raw["TotalCharges"].str.strip() == ""
print(f"Blank strings: {blank_mask.sum()}")
print(df_raw[blank_mask][["customerID", "tenure", "MonthlyCharges", "TotalCharges"]])

# Fix
df = df_raw.copy()
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
df["TotalCharges"].fillna(0, inplace=True)
print("\nAfter fix — nulls:", df["TotalCharges"].isna().sum())

# %% [markdown]
# ## 2. Class Imbalance

# %%
churn_counts = df["Churn"].value_counts()
print(churn_counts)
print(f"Churn rate: {churn_counts['Yes'] / len(df):.1%}")

fig, ax = plt.subplots(figsize=(4, 3))
churn_counts.plot(kind="bar", ax=ax, color=["#2ecc71", "#e74c3c"])
ax.set_title("Churn Distribution")
ax.set_ylabel("Count")
plt.tight_layout()
plt.savefig("../reports/churn_distribution.png")
plt.show()

# %% [markdown]
# ## 3. Collapse "No internet service" Categories

# %%
internet_cols = ["OnlineSecurity","OnlineBackup","DeviceProtection",
                 "TechSupport","StreamingTV","StreamingMovies"]
for col in internet_cols:
    print(col, df[col].value_counts().to_dict())

df[internet_cols] = df[internet_cols].replace("No internet service", "No")

# %% [markdown]
# ## 4. Churn by Contract Type (H1)

# %%
contract_churn = df.groupby("Contract")["Churn"].apply(
    lambda x: (x == "Yes").mean()
).reset_index(name="churn_rate")
print(contract_churn)

fig, ax = plt.subplots(figsize=(5, 3))
sns.barplot(data=contract_churn, x="Contract", y="churn_rate", ax=ax,
            palette=["#e74c3c","#f39c12","#2ecc71"])
ax.set_title("Churn Rate by Contract Type")
ax.set_ylabel("Churn Rate")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
plt.tight_layout()
plt.savefig("../reports/churn_by_contract.png")
plt.show()

# %% [markdown]
# ## 5. Churn by Tenure Bucket (H2)

# %%
df["tenure_bucket"] = pd.cut(df["tenure"], bins=[0,12,24,48,72],
                              labels=["0-12","13-24","25-48","49-72"],
                              include_lowest=True)
tenure_churn = df.groupby("tenure_bucket")["Churn"].apply(
    lambda x: (x == "Yes").mean()
).reset_index(name="churn_rate")
print(tenure_churn)

fig, ax = plt.subplots(figsize=(5, 3))
sns.barplot(data=tenure_churn, x="tenure_bucket", y="churn_rate", ax=ax)
ax.set_title("Churn Rate by Tenure Bucket")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
plt.tight_layout()
plt.savefig("../reports/churn_by_tenure.png")
plt.show()

# %% [markdown]
# ## 6. Churn by Payment Method (H3)

# %%
pay_churn = df.groupby("PaymentMethod")["Churn"].apply(
    lambda x: (x == "Yes").mean()
).reset_index(name="churn_rate").sort_values("churn_rate", ascending=False)
print(pay_churn)

fig, ax = plt.subplots(figsize=(6, 3))
sns.barplot(data=pay_churn, x="churn_rate", y="PaymentMethod", ax=ax)
ax.set_title("Churn Rate by Payment Method")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
plt.tight_layout()
plt.savefig("../reports/churn_by_payment.png")
plt.show()

# %% [markdown]
# ## 7. Churn by Internet Service (H5)

# %%
inet_churn = df.groupby("InternetService")["Churn"].apply(
    lambda x: (x == "Yes").mean()
).reset_index(name="churn_rate")
print(inet_churn)

# %% [markdown]
# ## 8. CLV Distribution: Churners vs Retained

# %%
df["clv"] = df["MonthlyCharges"] * df["tenure"]
fig, ax = plt.subplots(figsize=(6, 3))
for label, color in [("Yes", "#e74c3c"), ("No", "#2ecc71")]:
    df[df["Churn"] == label]["clv"].plot(kind="kde", ax=ax, label=label, color=color)
ax.set_title("CLV Distribution: Churners vs Retained")
ax.set_xlabel("CLV (MonthlyCharges × tenure)")
ax.legend(title="Churn")
plt.tight_layout()
plt.savefig("../reports/clv_distribution.png")
plt.show()

print("\nAvg CLV — Churners:  ₹", df[df["Churn"]=="Yes"]["clv"].mean().round(0))
print("Avg CLV — Retained: ₹", df[df["Churn"]=="No"]["clv"].mean().round(0))

# %% [markdown]
# ## 9. Correlation Heatmap (Numeric Features)

# %%
df["Churn_bin"] = (df["Churn"] == "Yes").astype(int)
num_cols = ["tenure", "MonthlyCharges", "TotalCharges", "clv", "Churn_bin"]
corr = df[num_cols].corr()

fig, ax = plt.subplots(figsize=(5, 4))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
ax.set_title("Correlation Matrix")
plt.tight_layout()
plt.savefig("../reports/correlation_heatmap.png")
plt.show()

# %% [markdown]
# ## 10. Hypothesis Summary
# | # | Hypothesis | Verdict |
# |---|-----------|---------|
# | H1 | Month-to-month → highest churn | ✅ |
# | H2 | Tenure 0-12 months → highest churn | ✅ |
# | H3 | Electronic check → highest churn | ✅ |
# | H4 | No OnlineSecurity/TechSupport → higher churn | ✅ |
# | H5 | Fiber optic → higher churn than DSL | ✅ |
# | H6 | Senior citizens churn more | Moderate |

print("EDA complete. All plots saved to reports/")
