"""
Phase 5 tests — verify tuning artifacts and safety constraints.

Run:
    cd dist/backend
    .venv311/Scripts/python.exe services/audio_custom/train/phase5_tests.py

All tests must PASS before proceeding to Phase 6.
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
MODELS_DIR = ROOT / "models"
METADATA_DIR = ROOT / "metadata"
FEATURES_DIR = ROOT / "features"

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []

LABEL_MAP = {"FAKE": 1, "REAL": 0}


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    msg = f"{status} {name}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results.append((name, condition))


# ---------------------------------------------------------------------------
# Load artifacts
# ---------------------------------------------------------------------------
with open(METADATA_DIR / "feature_schema.json") as f:
    schema = json.load(f)
feature_names = schema["feature_names"]

try:
    scaler = joblib.load(MODELS_DIR / "scaler.joblib")
    lr = joblib.load(MODELS_DIR / "logistic_regression.joblib")
    rf = joblib.load(MODELS_DIR / "random_forest.joblib")
    with open(MODELS_DIR / "tuning_summary.json") as f:
        tuning = json.load(f)
    artifacts_ok = True
except Exception as e:
    print(f"{FAIL} FATAL: Cannot load artifacts -- {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# T01: tuning_summary.json exists and has required keys
# ---------------------------------------------------------------------------
for key in ["phase", "test_loaded", "positive_class", "primary_metric",
            "phase4_baseline", "threshold_sweep", "rf_grid_search",
            "lr_c_sweep", "notes"]:
    check(f"T01-tuning-summary-has-{key}", key in tuning)

# ---------------------------------------------------------------------------
# T02: Test set was never loaded
# ---------------------------------------------------------------------------
check("T02-test-not-loaded", tuning["test_loaded"] is False,
      f"test_loaded={tuning['test_loaded']}")

# ---------------------------------------------------------------------------
# T03: RF model now has correct tuned params (n_est=200, max_depth=20, min_leaf=2)
# ---------------------------------------------------------------------------
check("T03-rf-n-estimators", rf.n_estimators == 200, f"n_estimators={rf.n_estimators}")
check("T03-rf-max-depth", rf.max_depth == 20, f"max_depth={rf.max_depth}")
check("T03-rf-min-samples-leaf", rf.min_samples_leaf == 2, f"min_samples_leaf={rf.min_samples_leaf}")

# ---------------------------------------------------------------------------
# T04: Tuned RF val FNR <= Phase 4 baseline (0.0021)
# ---------------------------------------------------------------------------
best_rf = tuning["rf_grid_search"]["best_config"]
check("T04-rf-val-fnr-improved", best_rf["val_fnr"] <= 0.0021,
      f"tuned_fnr={best_rf['val_fnr']:.4f} baseline=0.0021")
check("T04-rf-overwritten", tuning["rf_grid_search"]["rf_overwritten"] is True)

# ---------------------------------------------------------------------------
# T05: Tuned RF val metrics still strong
# ---------------------------------------------------------------------------
check("T05-rf-val-accuracy>=0.99", best_rf["val_accuracy"] >= 0.99,
      f"accuracy={best_rf['val_accuracy']:.4f}")
check("T05-rf-val-roc-auc>=0.99", best_rf["val_roc_auc"] >= 0.99,
      f"roc_auc={best_rf['val_roc_auc']:.4f}")
check("T05-rf-val-fpr<=0.01", best_rf["val_fpr"] <= 0.01,
      f"fpr={best_rf['val_fpr']:.4f}")

# ---------------------------------------------------------------------------
# T06: LR was NOT overwritten (best C tied with baseline — Phase 4 retained)
# ---------------------------------------------------------------------------
check("T06-lr-not-overwritten", tuning["lr_c_sweep"]["lr_overwritten"] is False)
best_lr = tuning["lr_c_sweep"]["best_config"]
check("T06-lr-best-fnr<=0.02", best_lr["val_fnr"] <= 0.02,
      f"fnr={best_lr['val_fnr']:.4f}")

# ---------------------------------------------------------------------------
# T07: Threshold sweep — verify best threshold respects FPR <= 10% constraint
# ---------------------------------------------------------------------------
best_thresh = tuning["threshold_sweep"]["best_entry_fpr_leq_10pct"]
check("T07-best-thresh-fpr<=0.10", best_thresh["fpr"] <= 0.10,
      f"fpr={best_thresh['fpr']:.4f}")
check("T07-best-thresh-fnr<baseline", best_thresh["fnr"] <= 0.0021,
      f"fnr={best_thresh['fnr']:.4f}")

# ---------------------------------------------------------------------------
# T08: Threshold sweep has 17 entries (0.10 to 0.90 step 0.05)
# ---------------------------------------------------------------------------
n_thresh = len(tuning["threshold_sweep"]["results"])
check("T08-threshold-sweep-count", n_thresh == 17, f"n={n_thresh}")

# ---------------------------------------------------------------------------
# T09: RF grid has 18 entries (2 x 3 x 3)
# ---------------------------------------------------------------------------
n_grid = len(tuning["rf_grid_search"]["results"])
check("T09-grid-result-count", n_grid == 18, f"n={n_grid}")

# ---------------------------------------------------------------------------
# T10: LR C sweep has 7 entries
# ---------------------------------------------------------------------------
n_lr = len(tuning["lr_c_sweep"]["results"])
check("T10-lr-sweep-count", n_lr == 7, f"n={n_lr}")

# ---------------------------------------------------------------------------
# T11: Reload tuned RF and predict on val — confirms model is valid
# ---------------------------------------------------------------------------
try:
    df_val = pd.read_csv(FEATURES_DIR / "validation_features.csv")
    X_val = df_val[feature_names].values.astype(np.float64)
    y_val = df_val["label"].map(LABEL_MAP).values

    rf_prob = rf.predict_proba(X_val)[:, 1]
    rf_pred = (rf_prob >= 0.5).astype(int)

    from sklearn.metrics import confusion_matrix, roc_auc_score
    tn, fp, fn, tp = confusion_matrix(y_val, rf_pred, labels=[0, 1]).ravel()
    fnr_live = fn / (tp + fn) if (tp + fn) > 0 else 0.0
    auc_live = roc_auc_score(y_val, rf_prob)

    check("T11-live-rf-fnr<=0.002", fnr_live <= 0.002,
          f"fnr={fnr_live:.4f}")
    check("T11-live-rf-auc>=0.999", auc_live >= 0.999,
          f"auc={auc_live:.4f}")
    check("T11-live-cm-total", (tn + fp + fn + tp) == len(y_val),
          f"total={tn+fp+fn+tp} n={len(y_val)}")
except Exception as e:
    check("T11-live-prediction", False, str(e))

# ---------------------------------------------------------------------------
# T12: Scaler still has 124 features
# ---------------------------------------------------------------------------
check("T12-scaler-feature-count", scaler.mean_.shape == (124,),
      f"shape={scaler.mean_.shape}")

# ---------------------------------------------------------------------------
# T13: Phase 4 models intact (training_summary.json still present)
# ---------------------------------------------------------------------------
check("T13-training-summary-exists", (MODELS_DIR / "training_summary.json").exists())

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
print()
n_pass = sum(1 for _, ok in results if ok)
n_fail = sum(1 for _, ok in results if not ok)
print(f"Phase 5 Tests: {n_pass}/{len(results)} PASS  {n_fail} FAIL")

if n_fail > 0:
    print("\nFailed tests:")
    for name, ok in results:
        if not ok:
            print(f"  {FAIL} {name}")
    sys.exit(1)
else:
    print("All Phase 5 tests PASSED.")
    sys.exit(0)
