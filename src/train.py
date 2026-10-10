"""
src/train.py — Train baseline + tuned models, log to MLflow
Run: python src/train.py
"""
import joblib
import mlflow
import mlflow.sklearn
import optuna
import warnings
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from features import prepare_data, build_preprocessor

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
SCALE_POS = 5174 / 1869  # neg/pos ratio for XGB/LGBM


def make_pipeline(clf) -> Pipeline:
    return Pipeline([("pre", build_preprocessor()), ("clf", clf)])


def cv_score(pipe, X, y, metric="roc_auc") -> float:
    return cross_val_score(pipe, X, y, cv=CV, scoring=metric, n_jobs=-1).mean()


def train_baseline(X, y):
    mlflow.set_experiment("telco-churn")
    with mlflow.start_run(run_name="baseline-logistic-regression"):
        pipe = make_pipeline(LogisticRegression(class_weight="balanced", max_iter=1000))
        auc = cv_score(pipe, X, y)
        f1  = cv_score(pipe, X, y, "f1")
        mlflow.log_metrics({"roc_auc": auc, "f1": f1})
        pipe.fit(X, y)
        mlflow.sklearn.log_model(pipe, "model")
        joblib.dump(pipe, "models/baseline_lr.pkl")
        print(f"[Baseline LR]  ROC-AUC={auc:.4f}  F1={f1:.4f}")
    return pipe


def tune_xgb(X, y):
    def objective(trial):
        params = {
            "n_estimators":     trial.suggest_int("n_estimators", 100, 500),
            "max_depth":        trial.suggest_int("max_depth", 3, 8),
            "learning_rate":    trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample":        trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "scale_pos_weight": SCALE_POS,
            "eval_metric": "logloss",
            "use_label_encoder": False,
            "random_state": 42,
        }
        pipe = make_pipeline(XGBClassifier(**params))
        return cv_score(pipe, X, y)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=30, show_progress_bar=True)

    best = study.best_params
    best.update({"scale_pos_weight": SCALE_POS, "eval_metric": "logloss",
                 "use_label_encoder": False, "random_state": 42})

    mlflow.set_experiment("telco-churn")
    with mlflow.start_run(run_name="xgboost-optuna"):
        pipe = make_pipeline(XGBClassifier(**best))
        auc = cv_score(pipe, X, y)
        f1  = cv_score(pipe, X, y, "f1")
        mlflow.log_params(best)
        mlflow.log_metrics({"roc_auc": auc, "f1": f1})
        pipe.fit(X, y)
        mlflow.sklearn.log_model(pipe, "model")
        joblib.dump(pipe, "models/xgb_best.pkl")
        print(f"[XGBoost]      ROC-AUC={auc:.4f}  F1={f1:.4f}")
    return pipe


def tune_lgbm(X, y):
    def objective(trial):
        params = {
            "n_estimators":  trial.suggest_int("n_estimators", 100, 500),
            "max_depth":     trial.suggest_int("max_depth", 3, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "num_leaves":    trial.suggest_int("num_leaves", 20, 100),
            "class_weight":  "balanced",
            "random_state":  42,
            "verbose": -1,
        }
        pipe = make_pipeline(LGBMClassifier(**params))
        return cv_score(pipe, X, y)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=30, show_progress_bar=True)

    best = study.best_params
    best.update({"class_weight": "balanced", "random_state": 42, "verbose": -1})

    mlflow.set_experiment("telco-churn")
    with mlflow.start_run(run_name="lightgbm-optuna"):
        pipe = make_pipeline(LGBMClassifier(**best))
        auc = cv_score(pipe, X, y)
        f1  = cv_score(pipe, X, y, "f1")
        mlflow.log_params(best)
        mlflow.log_metrics({"roc_auc": auc, "f1": f1})
        pipe.fit(X, y)
        mlflow.sklearn.log_model(pipe, "model")
        joblib.dump(pipe, "models/lgbm_best.pkl")
        print(f"[LightGBM]     ROC-AUC={auc:.4f}  F1={f1:.4f}")
    return pipe


if __name__ == "__main__":
    X, y = prepare_data()
    train_baseline(X, y)
    tune_xgb(X, y)
    tune_lgbm(X, y)
    print("\nAll models saved to models/. View runs: mlflow ui")
