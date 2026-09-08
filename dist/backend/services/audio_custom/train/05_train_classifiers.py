"""
Phase 4 — Train Classifiers
============================
Trains two classifiers on FOR-2sec acoustic features:
  1. Logistic Regression  (baseline, scaled)
  2. Random Forest        (primary, unscaled + scaled)

Rules
-----
- Scaler is fit ONLY on X_train; applied to val for reporting.
- Test set is NEVER loaded here (Phase 6 only).
- No hyperparameter tuning from val metrics (Phase 5 task).
- Labels: "FAKE" -> 1, "REAL" -> 0  (FAKE is the positive class)
- Primary metric: FNR = FP_fake_classified_as_real / total_fake
  (FAKE predicted as REAL is the safety-critical error)

Outputs (models/)
-----------------
  scaler.joblib               StandardScaler fit on X_train
  logistic_regression.joblib  LogisticRegression(C=1, max_iter=1000)
  random_forest.joblib        RandomForestClassifier(n_estimators=400, ...)
  training_summary.json       all metrics + metadata
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
FEATURES_DIR = ROOT / "features"
MODELS_DIR = ROOT / "models"
METADATA_DIR = ROOT / "metadata"

MODELS_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_CSV = FEATURES_DIR / "train_features.csv"
VAL_CSV = FEATURES_DIR / "validation_features.csv"
SCHEMA_JSON = METADATA_DIR / "feature_schema.json"

# ---------------------------------------------------------------------------
# Label encoding: FAKE=1 (positive class), REAL=0
# ---------------------------------------------------------------------------
LABEL_MAP = {"FAKE": 1, "REAL": 0}
BOOKKEEPING_COLS = {"file_id", "split", "label"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_split(csv_path: Path, feature_names: list[str]) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Load a CSV split, return (X, y, df_meta)."""
    df = pd.read_csv(csv_path)
    missing = [f for f in feature_names if f not in df.columns]
    if missing:
        raise ValueError(f"Missing features in {csv_path.name}: {missing}")
    X = df[feature_names].values.astype(np.float64)
    y = df["label"].map(LABEL_MAP).values
    if np.any(np.isnan(X)) or np.any(np.isinf(X)):
        raise ValueError(f"NaN/Inf found in {csv_path.name}")
    return X, y, df[list(BOOKKEEPING_COLS & set(df.columns))]


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray, split_name: str) -> dict:
    """
    Compute full metric set.

    FAKE=1 is the positive class.
    FNR = missed detections (FAKE predicted as REAL) / total FAKE
    FPR = false alarms (REAL predicted as FAKE) / total REAL
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    n_fake = tp + fn
    n_real = tn + fp
    fnr = fn / n_fake if n_fake > 0 else 0.0
    fpr = fp / n_real if n_real > 0 else 0.0
    return {
        "split": split_name,
        "n_samples": int(len(y_true)),
        "n_fake": int(n_fake),
        "n_real": int(n_real),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 6),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 6),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 6),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 6),
        "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 6),
        "fpr": round(float(fpr), 6),
        "fnr": round(float(fnr), 6),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def print_metrics(label: str, m: dict) -> None:
    print(f"\n  [{label}] {m['split'].upper()} — n={m['n_samples']}")
    print(f"    Accuracy : {m['accuracy']:.4f}")
    print(f"    Precision: {m['precision']:.4f}  Recall: {m['recall']:.4f}  F1: {m['f1']:.4f}")
    print(f"    ROC-AUC  : {m['roc_auc']:.4f}")
    print(f"    FPR      : {m['fpr']:.4f}  FNR (primary): {m['fnr']:.4f}")
    cm = m["confusion_matrix"]
    print(f"    Confusion : TN={cm['tn']} FP={cm['fp']} FN={cm['fn']} TP={cm['tp']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("ADIS Phase 4 — Training Classifiers")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Load feature schema
    # ------------------------------------------------------------------
    with open(SCHEMA_JSON) as f:
        schema = json.load(f)
    feature_names: list[str] = schema["feature_names"]
    assert len(feature_names) == 124, f"Expected 124 features, got {len(feature_names)}"
    print(f"\n[1/7] Feature schema loaded — {len(feature_names)} features")

    # ------------------------------------------------------------------
    # 2. Load train + val splits
    # ------------------------------------------------------------------
    print("[2/7] Loading splits ...")
    X_train, y_train, _ = load_split(TRAIN_CSV, feature_names)
    X_val, y_val, _ = load_split(VAL_CSV, feature_names)
    print(f"      Train : {X_train.shape} | FAKE={y_train.sum()} REAL={(y_train==0).sum()}")
    print(f"      Val   : {X_val.shape}   | FAKE={y_val.sum()} REAL={(y_val==0).sum()}")

    # Safety guard: test set must not be loaded here
    test_csv = FEATURES_DIR / "test_features.csv"
    assert test_csv.exists(), "test_features.csv not found (Phase 6 check)"
    # We deliberately DO NOT load it.

    # ------------------------------------------------------------------
    # 3. Fit scaler on X_train only
    # ------------------------------------------------------------------
    print("[3/7] Fitting StandardScaler on X_train ...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    scaler_path = MODELS_DIR / "scaler.joblib"
    joblib.dump(scaler, scaler_path)
    print(f"      Saved  : {scaler_path}")

    # ------------------------------------------------------------------
    # 4. Train Logistic Regression (baseline)
    # ------------------------------------------------------------------
    print("\n[4/7] Training Logistic Regression (baseline) ...")
    t0 = time.perf_counter()
    lr = LogisticRegression(
        C=1.0,
        max_iter=1000,
        solver="lbfgs",
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    lr.fit(X_train_scaled, y_train)
    lr_train_time = time.perf_counter() - t0
    print(f"      Train time: {lr_train_time:.2f}s")

    lr_path = MODELS_DIR / "logistic_regression.joblib"
    joblib.dump(lr, lr_path)
    print(f"      Saved  : {lr_path}")

    lr_train_prob = lr.predict_proba(X_train_scaled)[:, 1]
    lr_train_pred = lr.predict(X_train_scaled)
    lr_val_prob = lr.predict_proba(X_val_scaled)[:, 1]
    lr_val_pred = lr.predict(X_val_scaled)

    lr_m_train = compute_metrics(y_train, lr_train_pred, lr_train_prob, "train")
    lr_m_val = compute_metrics(y_val, lr_val_pred, lr_val_prob, "validation")
    print_metrics("LR", lr_m_train)
    print_metrics("LR", lr_m_val)

    # ------------------------------------------------------------------
    # 5. Train Random Forest (primary)
    # ------------------------------------------------------------------
    print("\n[5/7] Training Random Forest (primary, n_estimators=400) ...")
    t0 = time.perf_counter()
    rf = RandomForestClassifier(
        n_estimators=400,
        max_features="sqrt",
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)          # RF does NOT need scaling
    rf_train_time = time.perf_counter() - t0
    print(f"      Train time: {rf_train_time:.2f}s")

    rf_path = MODELS_DIR / "random_forest.joblib"
    joblib.dump(rf, rf_path)
    print(f"      Saved  : {rf_path}")

    rf_train_prob = rf.predict_proba(X_train)[:, 1]
    rf_train_pred = rf.predict(X_train)
    rf_val_prob = rf.predict_proba(X_val)[:, 1]
    rf_val_pred = rf.predict(X_val)

    rf_m_train = compute_metrics(y_train, rf_train_pred, rf_train_prob, "train")
    rf_m_val = compute_metrics(y_val, rf_val_pred, rf_val_prob, "validation")
    print_metrics("RF", rf_m_train)
    print_metrics("RF", rf_m_val)

    # ------------------------------------------------------------------
    # 6. Feature importance (top 20)
    # ------------------------------------------------------------------
    print("\n[6/7] RF Feature importance (top 20) ...")
    importances = rf.feature_importances_
    ranked = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
    top_20 = ranked[:20]
    for rank, (name, imp) in enumerate(top_20, 1):
        print(f"      {rank:2d}. {name:<45s} {imp:.5f}")

    # ------------------------------------------------------------------
    # 7. Save training summary
    # ------------------------------------------------------------------
    print("\n[7/7] Saving training_summary.json ...")
    summary = {
        "phase": "Phase 4 — Training",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "sklearn_version": __import__("sklearn").__version__,
        "joblib_version": joblib.__version__,
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "label_encoding": LABEL_MAP,
        "positive_class": "FAKE",
        "primary_metric": "FNR (FAKE classified as REAL)",
        "train_n": int(len(y_train)),
        "val_n": int(len(y_val)),
        "test_loaded": False,
        "logistic_regression": {
            "model_file": "logistic_regression.joblib",
            "params": lr.get_params(),
            "train_time_s": round(lr_train_time, 3),
            "metrics_train": lr_m_train,
            "metrics_val": lr_m_val,
        },
        "random_forest": {
            "model_file": "random_forest.joblib",
            "params": rf.get_params(),
            "train_time_s": round(rf_train_time, 3),
            "metrics_train": rf_m_train,
            "metrics_val": rf_m_val,
            "top_20_features": [
                {"rank": i + 1, "feature": name, "importance": round(float(imp), 6)}
                for i, (name, imp) in enumerate(top_20)
            ],
        },
        "scaler": {
            "model_file": "scaler.joblib",
            "type": "StandardScaler",
            "fit_on": "X_train only",
        },
        "overfitting_check": {
            "rf_accuracy_gap": round(rf_m_train["accuracy"] - rf_m_val["accuracy"], 6),
            "rf_fnr_gap": round(rf_m_train["fnr"] - rf_m_val["fnr"], 6),
            "lr_accuracy_gap": round(lr_m_train["accuracy"] - lr_m_val["accuracy"], 6),
        },
        "notes": [
            "Test set NOT loaded. Evaluation reserved for Phase 6.",
            "FNR is primary metric: FAKE predicted as REAL is the safety-critical error.",
            "RF is trained on unscaled features; LR on scaled.",
            "class_weight='balanced' applied to both models.",
        ],
    }

    summary_path = MODELS_DIR / "training_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"      Saved  : {summary_path}")

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("PHASE 4 COMPLETE — STOP REPORT")
    print("=" * 60)
    print(f"\n  LR  val accuracy={lr_m_val['accuracy']:.4f}  FNR={lr_m_val['fnr']:.4f}  ROC-AUC={lr_m_val['roc_auc']:.4f}")
    print(f"  RF  val accuracy={rf_m_val['accuracy']:.4f}  FNR={rf_m_val['fnr']:.4f}  ROC-AUC={rf_m_val['roc_auc']:.4f}")
    print(f"\n  Overfitting check (RF accuracy gap train-val): {summary['overfitting_check']['rf_accuracy_gap']:.4f}")
    print(f"  Overfitting check (RF FNR gap train-val):      {summary['overfitting_check']['rf_fnr_gap']:.4f}")
    print("\n  Artifacts saved:")
    print(f"    {scaler_path}")
    print(f"    {lr_path}")
    print(f"    {rf_path}")
    print(f"    {summary_path}")
    print("\n  Next: await user approval before Phase 5 (hyperparameter tuning on val only).")
    print("=" * 60)


if __name__ == "__main__":
    main()
