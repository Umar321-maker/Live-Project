"""
Download dataset from Kaggle.
Requires: pip install kaggle  +  ~/.kaggle/kaggle.json with API credentials
"""
import subprocess, sys, os

DATASET = "blastchar/telco-customer-churn"
OUT_DIR = "data/raw"

os.makedirs(OUT_DIR, exist_ok=True)
subprocess.run(
    [sys.executable, "-m", "kaggle", "datasets", "download",
     "-d", DATASET, "-p", OUT_DIR, "--unzip"],
    check=True,
)
print(f"Dataset downloaded to {OUT_DIR}/")
