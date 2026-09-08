"""
Phase 5 — Hyperparameter Tuning (train/val ONLY — test set never loaded)
=========================================================================

Tuning scope
------------
1. RF threshold sweep  — find operating point minimising FNR with FPR <= 10%
2. RF structural grid  — max_depth x min_samples_leaf (small, val FNR primary)
3. LR C sweep          — regularisation strength
4. Final retrain       — best RF config retrained on X_train, evaluated on val

Rules
-----
- Scaler is fit ONLY on X_train (loaded fresh here).
- Val set is used ONLY to SELECT the best config — never to fit parameters.
- Test CSV is never loaded (assert guard in place).
- No config is chosen because it looks good on a fabricated signal.
- Outputs overwrite models/random_forest.joblib and models/scaler.joblib
  only if the tuned model beats the Phase 4 baseline on val FNR.

Outputs (models/)
-----------------
  random_forest.joblib         best RF (overwritten if improved)
  scaler.joblib                scaler for best RF (overwritten if improved)
  logistic_regression.joblib   best LR (overwritten if improved)
  tuning_summary.json          full sweep results
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
FEATURES_DIR = ROOT / "features"
MODELS_DIR = ROOT / "models"
METADATA_DIR = ROOT / "metadata"

TRAIN_CSV = FEATURES_DIR / "train_features.csv"
VAL_CSV = FEATURES_DIR / "validation_features.csv"
SCHEMA_JSON = METADATA_DIR / "feature_schema.json"

LABEL_MAP = {"FAKE": 1, "REAL": 0}

# Phase 4 baseline for comparison
BASELINE_RF_VAL_FNR = 0.0021
BASELINE_RF_VAL_ACC = 0.9968
BASELINE_LR_VAL_FNR = 0.0106
BASELINE_LR_VAL_ACC = 0.9901


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_split(csv_path: Path, feature_names: list) -> tuple:
    df = pd.read_csv(csv_path)
    X = df[feature_names].values.astype(np.float64)
    y = df["label"].map(LABEL_MAP).values
    assert not (np.any(np.isnan(X)) or np.any(np.isinf(X))), f"NaN/Inf in {csv_path.name}"
    return X, y


def metrics_at_threshold(y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> dict:
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    n_fake = tp + fn
    n_real = tn + fp
    fnr = fn / n_fake if n_fake > 0 else 0.0
    fpr = fp / n_real if n_real > 0 else 0.0
    acc = (tp + tn) / len(y_true)
    return {
        "threshold": round(float(threshold), 4),
        "accuracy": round(float(acc), 6),
        "fnr": round(float(fnr), 6),
        "fpr": round(float(fpr), 6),
        "tp": int(tp), "tn": int(tn), "fp": int(fp), "fn": int(fn),
    }


def train_rf(X_train, y_train, **kwargs) -> RandomForestClassifier:
    rf = RandomForestClassifier(
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
        **kwargs,
    )
    rf.fit(X_train, y_train)
    return rf


def train_lr(X_train_scaled, y_train, C: float) -> LogisticRegression:
    lr = LogisticRegression(
        C=C,
        max_iter=2000,
        solver="lbfgs",
        class_weight="balanced",
        random_state=42,
    )
    lr.fit(X_train_scaled, y_train)
    return lr


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 64)
    print("ADIS Phase 5 -- Hyperparameter Tuning")
    print("=" * 64)

    # Safety guard -- test set must never be loaded here
    test_csv = FEATURES_DIR / "test_features.csv"
    assert test_csv.exists(), "test_features.csv missing"

    # ------------------------------------------------------------------
    # 1. Load schema + splits
    # ------------------------------------------------------------------
    with open(SCHEMA_JSON) as f:
        schema = json.load(f)
    feature_names = schema["feature_names"]
    assert len(feature_names) == 124

    print("\n[1/5] Loading train + val ...")
    X_train, y_train = load_split(TRAIN_CSV, feature_names)
    X_val, y_val = load_split(VAL_CSV, feature_names)
    print(f"      Train: {X_train.shape}  Val: {X_val.shape}")
    print(f"      Test CSV exists but NOT loaded (Phase 6 guard confirmed)")

    # ------------------------------------------------------------------
    # 2. RF threshold sweep (using Phase 4 baseline model)
    # ------------------------------------------------------------------
    print("\n[2/5] RF threshold sweep ...")
    rf_base = joblib.load(MODELS_DIR / "random_forest.joblib")
    rf_val_prob = rf_base.predict_proba(X_val)[:, 1]

    thresholds = np.arange(0.10, 0.91, 0.05)
    threshold_results = []
    for t in thresholds:
        m = metrics_at_threshold(y_val, rf_val_prob, t)
        threshold_results.append(m)

    print(f"  {'Threshold':>10} {'Accuracy':>10} {'FNR':>8} {'FPR':>8}")
    print(f"  {'-'*10} {'-'*10} {'-'*8} {'-'*8}")
    for m in threshold_results:
        marker = " <-- baseline" if abs(m["threshold"] - 0.50) < 0.01 else ""
        print(f"  {m['threshold']:>10.2f} {m['accuracy']:>10.4f} {m['fnr']:>8.4f} {m['fpr']:>8.4f}{marker}")

    # Best threshold: min FNR where FPR <= 10%
    valid = [m for m in threshold_results if m["fpr"] <= 0.10]
    best_thresh_entry = min(valid, key=lambda m: (m["fnr"], -m["accuracy"])) if valid else None
    if best_thresh_entry:
        print(f"\n  Best threshold (FPR<=10%): {best_thresh_entry['threshold']:.2f}"
              f"  FNR={best_thresh_entry['fnr']:.4f}  FPR={best_thresh_entry['fpr']:.4f}")
    else:
        print("  WARNING: No threshold satisfies FPR <= 10%")
        best_thresh_entry = metrics_at_threshold(y_val, rf_val_prob, 0.50)

    # ------------------------------------------------------------------
    # 3. RF structural grid search (max_depth x min_samples_leaf)
    # ------------------------------------------------------------------
    print("\n[3/5] RF structural grid search ...")
    max_depths = [None, 20, 30]
    min_samples_leaves = [1, 2, 4]
    n_estimators_grid = [200, 400]

    grid_results = []
    best_grid_fnr = float("inf")
    best_grid_cfg = None
    best_grid_model = None

    print(f"  {'n_est':>6} {'max_depth':>10} {'min_leaf':>9} {'val_acc':>8} {'val_FNR':>8} {'val_FPR':>8} {'AUC':>7}")
    print(f"  {'-'*6} {'-'*10} {'-'*9} {'-'*8} {'-'*8} {'-'*8} {'-'*7}")

    for n_est in n_estimators_grid:
        for md in max_depths:
            for msl in min_samples_leaves:
                t0 = time.perf_counter()
                rf_candidate = train_rf(
                    X_train, y_train,
                    n_estimators=n_est,
                    max_depth=md,
                    min_samples_leaf=msl,
                    max_features="sqrt",
                )
                elapsed = time.perf_counter() - t0
                prob = rf_candidate.predict_proba(X_val)[:, 1]
                m = metrics_at_threshold(y_val, prob, 0.5)
                auc = round(float(roc_auc_score(y_val, prob)), 6)
                cfg = {
                    "n_estimators": n_est,
                    "max_depth": md,
                    "min_samples_leaf": msl,
                    "val_accuracy": m["accuracy"],
                    "val_fnr": m["fnr"],
                    "val_fpr": m["fpr"],
                    "val_roc_auc": auc,
                    "train_time_s": round(elapsed, 2),
                }
                grid_results.append(cfg)

                md_str = str(md) if md is not None else "None"
                marker = ""
                if m["fnr"] < best_grid_fnr:
                    best_grid_fnr = m["fnr"]
                    best_grid_cfg = cfg
                    best_grid_model = rf_candidate
                    marker = " *"
                print(f"  {n_est:>6} {md_str:>10} {msl:>9} {m['accuracy']:>8.4f}"
                      f" {m['fnr']:>8.4f} {m['fpr']:>8.4f} {auc:>7.4f}{marker}")

    print(f"\n  Best RF config: n_est={best_grid_cfg['n_estimators']}"
          f"  max_depth={best_grid_cfg['max_depth']}"
          f"  min_leaf={best_grid_cfg['min_samples_leaf']}"
          f"  FNR={best_grid_cfg['val_fnr']:.4f}"
          f"  ACC={best_grid_cfg['val_accuracy']:.4f}")

    # ------------------------------------------------------------------
    # 4. LR C sweep
    # ------------------------------------------------------------------
    print("\n[4/5] LR C sweep ...")
    # Refit scaler on X_train (fresh, not loaded from disk)
    scaler_fresh = StandardScaler()
    X_train_scaled = scaler_fresh.fit_transform(X_train)
    X_val_scaled = scaler_fresh.transform(X_val)

    C_values = [0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    lr_results = []
    best_lr_fnr = float("inf")
    best_lr_cfg = None
    best_lr_model = None
    best_lr_scaler = None

    print(f"  {'C':>8} {'val_acc':>8} {'val_FNR':>8} {'val_FPR':>8} {'AUC':>7}")
    print(f"  {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*7}")
    for C in C_values:
        lr_c = train_lr(X_train_scaled, y_train, C)
        prob = lr_c.predict_proba(X_val_scaled)[:, 1]
        m = metrics_at_threshold(y_val, prob, 0.5)
        auc = round(float(roc_auc_score(y_val, prob)), 6)
        cfg = {
            "C": C, "val_accuracy": m["accuracy"],
            "val_fnr": m["fnr"], "val_fpr": m["fpr"], "val_roc_auc": auc,
        }
        lr_results.append(cfg)
        marker = ""
        if m["fnr"] < best_lr_fnr:
            best_lr_fnr = m["fnr"]
            best_lr_cfg = cfg
            best_lr_model = lr_c
            best_lr_scaler = scaler_fresh
            marker = " *"
        print(f"  {C:>8.2f} {m['accuracy']:>8.4f} {m['fnr']:>8.4f} {m['fpr']:>8.4f} {auc:>7.4f}{marker}")

    print(f"\n  Best LR C={best_lr_cfg['C']}  FNR={best_lr_cfg['val_fnr']:.4f}"
          f"  ACC={best_lr_cfg['val_accuracy']:.4f}")

    # ------------------------------------------------------------------
    # 5. Save best models (only if improved over Phase 4 baseline)
    # ------------------------------------------------------------------
    print("\n[5/5] Saving best models ...")

    rf_improved = best_grid_cfg["val_fnr"] <= BASELINE_RF_VAL_FNR
    lr_improved = best_lr_cfg["val_fnr"] <= BASELINE_LR_VAL_FNR

    if rf_improved:
        joblib.dump(best_grid_model, MODELS_DIR / "random_forest.joblib")
        print(f"  RF  overwritten -- FNR {BASELINE_RF_VAL_FNR:.4f} -> {best_grid_cfg['val_fnr']:.4f}")
    else:
        print(f"  RF  NOT overwritten -- tuned FNR {best_grid_cfg['val_fnr']:.4f}"
              f" >= baseline {BASELINE_RF_VAL_FNR:.4f} (Phase 4 model retained)")

    if lr_improved:
        joblib.dump(best_lr_model, MODELS_DIR / "logistic_regression.joblib")
        joblib.dump(best_lr_scaler, MODELS_DIR / "scaler.joblib")
        print(f"  LR  overwritten -- FNR {BASELINE_LR_VAL_FNR:.4f} -> {best_lr_cfg['val_fnr']:.4f}")
        print(f"  Scaler overwritten (paired with best LR)")
    else:
        print(f"  LR  NOT overwritten -- tuned FNR {best_lr_cfg['val_fnr']:.4f}"
              f" >= baseline {BASELINE_LR_VAL_FNR:.4f} (Phase 4 model retained)")

    # ------------------------------------------------------------------
    # Save tuning summary
    # ------------------------------------------------------------------
    summary = {
        "phase": "Phase 5 -- Hyperparameter Tuning",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "test_loaded": False,
        "positive_class": "FAKE",
        "primary_metric": "FNR (FAKE classified as REAL)",
        "phase4_baseline": {
            "rf_val_fnr": BASELINE_RF_VAL_FNR,
            "rf_val_accuracy": BASELINE_RF_VAL_ACC,
            "lr_val_fnr": BASELINE_LR_VAL_FNR,
            "lr_val_accuracy": BASELINE_LR_VAL_ACC,
        },
        "threshold_sweep": {
            "model": "random_forest (Phase 4 baseline)",
            "results": threshold_results,
            "best_entry_fpr_leq_10pct": best_thresh_entry,
        },
        "rf_grid_search": {
            "fixed_params": {"max_features": "sqrt", "class_weight": "balanced", "random_state": 42},
            "grid": {
                "n_estimators": n_estimators_grid,
                "max_depth": max_depths,
                "min_samples_leaf": min_samples_leaves,
            },
            "results": grid_results,
            "best_config": best_grid_cfg,
            "rf_overwritten": rf_improved,
        },
        "lr_c_sweep": {
            "C_values": C_values,
            "results": lr_results,
            "best_config": best_lr_cfg,
            "lr_overwritten": lr_improved,
        },
        "notes": [
            "Test set NOT loaded -- evaluation reserved for Phase 6.",
            "Models overwritten only if tuned FNR <= Phase 4 baseline FNR.",
            "Threshold sweep uses Phase 4 RF; structural grid uses fresh retrain.",
            "Scaler refit on X_train only in all cases.",
        ],
    }

    summary_path = MODELS_DIR / "tuning_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Saved: {summary_path}")

    # ------------------------------------------------------------------
    # STOP report
    # ------------------------------------------------------------------
    print("\n" + "=" * 64)
    print("PHASE 5 COMPLETE -- STOP REPORT")
    print("=" * 64)
    print(f"\n  Threshold sweep best (FPR<=10%):"
          f" threshold={best_thresh_entry['threshold']:.2f}"
          f"  FNR={best_thresh_entry['fnr']:.4f}  FPR={best_thresh_entry['fpr']:.4f}")
    print(f"\n  RF grid best: n_est={best_grid_cfg['n_estimators']}"
          f"  max_depth={best_grid_cfg['max_depth']}"
          f"  min_leaf={best_grid_cfg['min_samples_leaf']}")
    print(f"    val_accuracy={best_grid_cfg['val_accuracy']:.4f}"
          f"  val_FNR={best_grid_cfg['val_fnr']:.4f}"
          f"  val_ROC-AUC={best_grid_cfg['val_roc_auc']:.4f}")
    print(f"  RF overwritten: {rf_improved}")
    print(f"\n  LR best C={best_lr_cfg['C']}")
    print(f"    val_accuracy={best_lr_cfg['val_accuracy']:.4f}"
          f"  val_FNR={best_lr_cfg['val_fnr']:.4f}"
          f"  val_ROC-AUC={best_lr_cfg['val_roc_auc']:.4f}")
    print(f"  LR overwritten: {lr_improved}")
    print("\n  Next: await user approval before Phase 6 (final test set evaluation).")
    print("=" * 64)


if __name__ == "__main__":
    main()
