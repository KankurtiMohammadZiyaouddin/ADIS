"""
Phase 4 tests — verify training artifacts and metrics.

Run:
    cd dist/backend
    .venv311/Scripts/python.exe services/audio_custom/train/phase4_tests.py

All tests must PASS before proceeding to Phase 5.
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
MODELS_DIR = ROOT / "models"
METADATA_DIR = ROOT / "metadata"

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    msg = f"{status} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append((name, condition))


# ---------------------------------------------------------------------------
# T01: All model files exist
# ---------------------------------------------------------------------------
for fname in ["scaler.joblib", "logistic_regression.joblib", "random_forest.joblib", "training_summary.json"]:
    p = MODELS_DIR / fname
    check(f"T01-{fname}-exists", p.exists(), str(p))

# ---------------------------------------------------------------------------
# T02: Models load without error
# ---------------------------------------------------------------------------
try:
    scaler = joblib.load(MODELS_DIR / "scaler.joblib")
    lr = joblib.load(MODELS_DIR / "logistic_regression.joblib")
    rf = joblib.load(MODELS_DIR / "random_forest.joblib")
    check("T02-models-load", True)
except Exception as e:
    check("T02-models-load", False, str(e))
    print("FATAL: Cannot load models. Aborting.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# T03: Scaler was fit on 124 features
# ---------------------------------------------------------------------------
check("T03-scaler-feature-count", scaler.mean_.shape == (124,), f"shape={scaler.mean_.shape}")

# ---------------------------------------------------------------------------
# T04: LR input/output shape
# ---------------------------------------------------------------------------
check("T04-lr-coef-shape", lr.coef_.shape == (1, 124), f"shape={lr.coef_.shape}")
check("T04-lr-classes", list(lr.classes_) == [0, 1], f"classes={lr.classes_}")

# ---------------------------------------------------------------------------
# T05: RF input/output shape
# ---------------------------------------------------------------------------
check("T05-rf-n-estimators", rf.n_estimators == 400, f"n_estimators={rf.n_estimators}")
check("T05-rf-classes", list(rf.classes_) == [0, 1], f"classes={rf.classes_}")

# ---------------------------------------------------------------------------
# T06: Predict on dummy input — must not crash
# ---------------------------------------------------------------------------
x_dummy = np.zeros((1, 124))
try:
    lr_pred = lr.predict(scaler.transform(x_dummy))
    rf_pred = rf.predict(x_dummy)
    lr_prob = lr.predict_proba(scaler.transform(x_dummy))
    rf_prob = rf.predict_proba(x_dummy)
    check("T06-predict-smoke", True)
    check("T06-lr-prob-shape", lr_prob.shape == (1, 2), f"shape={lr_prob.shape}")
    check("T06-rf-prob-shape", rf_prob.shape == (1, 2), f"shape={rf_prob.shape}")
    check("T06-lr-prob-sums-to-1", abs(lr_prob[0].sum() - 1.0) < 1e-6, f"sum={lr_prob[0].sum()}")
    check("T06-rf-prob-sums-to-1", abs(rf_prob[0].sum() - 1.0) < 1e-6, f"sum={rf_prob[0].sum()}")
except Exception as e:
    check("T06-predict-smoke", False, str(e))

# ---------------------------------------------------------------------------
# T07: training_summary.json structure + safety guard
# ---------------------------------------------------------------------------
with open(MODELS_DIR / "training_summary.json") as f:
    summary = json.load(f)

check("T07-test-not-loaded", summary["test_loaded"] is False, f"test_loaded={summary['test_loaded']}")
check("T07-feature-count", summary["feature_count"] == 124, f"feature_count={summary['feature_count']}")
check("T07-positive-class", summary["positive_class"] == "FAKE")
check("T07-has-lr-metrics", "metrics_val" in summary["logistic_regression"])
check("T07-has-rf-metrics", "metrics_val" in summary["random_forest"])

# ---------------------------------------------------------------------------
# T08: Validation metrics — LR meets minimum thresholds
# ---------------------------------------------------------------------------
lr_val = summary["logistic_regression"]["metrics_val"]
check("T08-lr-val-accuracy>=0.85", lr_val["accuracy"] >= 0.85, f"accuracy={lr_val['accuracy']:.4f}")
check("T08-lr-val-roc-auc>=0.85", lr_val["roc_auc"] >= 0.85, f"roc_auc={lr_val['roc_auc']:.4f}")
check("T08-lr-val-fnr<=0.20", lr_val["fnr"] <= 0.20, f"fnr={lr_val['fnr']:.4f}")

# ---------------------------------------------------------------------------
# T09: Validation metrics — RF meets minimum thresholds
# ---------------------------------------------------------------------------
rf_val = summary["random_forest"]["metrics_val"]
check("T09-rf-val-accuracy>=0.90", rf_val["accuracy"] >= 0.90, f"accuracy={rf_val['accuracy']:.4f}")
check("T09-rf-val-roc-auc>=0.90", rf_val["roc_auc"] >= 0.90, f"roc_auc={rf_val['roc_auc']:.4f}")
check("T09-rf-val-fnr<=0.15", rf_val["fnr"] <= 0.15, f"fnr={rf_val['fnr']:.4f}")
check("T09-rf-beats-lr-accuracy", rf_val["accuracy"] >= lr_val["accuracy"] - 0.01,
      f"rf={rf_val['accuracy']:.4f} lr={lr_val['accuracy']:.4f}")

# ---------------------------------------------------------------------------
# T10: Overfitting guard — RF train/val accuracy gap < 5%
# ---------------------------------------------------------------------------
rf_train = summary["random_forest"]["metrics_train"]
acc_gap = rf_train["accuracy"] - rf_val["accuracy"]
check("T10-rf-overfit-accuracy-gap<0.05", acc_gap < 0.05, f"gap={acc_gap:.4f}")

# ---------------------------------------------------------------------------
# T11: Confusion matrix structure
# ---------------------------------------------------------------------------
rf_cm = rf_val["confusion_matrix"]
for k in ("tn", "fp", "fn", "tp"):
    check(f"T11-rf-cm-has-{k}", k in rf_cm)
total = rf_cm["tn"] + rf_cm["fp"] + rf_cm["fn"] + rf_cm["tp"]
check("T11-rf-cm-total-matches-n", total == rf_val["n_samples"], f"total={total} n={rf_val['n_samples']}")

# ---------------------------------------------------------------------------
# T12: Feature schema matches model
# ---------------------------------------------------------------------------
with open(METADATA_DIR / "feature_schema.json") as f:
    schema = json.load(f)
schema_names = schema["feature_names"]
check("T12-schema-feature-count", len(schema_names) == 124, f"n={len(schema_names)}")
check("T12-summary-features-match-schema", summary["feature_names"] == schema_names)

# ---------------------------------------------------------------------------
# T13: Label encoding correct
# ---------------------------------------------------------------------------
check("T13-label-FAKE=1", summary["label_encoding"]["FAKE"] == 1)
check("T13-label-REAL=0", summary["label_encoding"]["REAL"] == 0)

# ---------------------------------------------------------------------------
# T14: No test features were used
# ---------------------------------------------------------------------------
test_csv = ROOT / "features" / "test_features.csv"
check("T14-test-csv-exists-but-unused", test_csv.exists(), "test CSV must exist for Phase 6")
# Confirm training_summary explicitly records test_loaded=False
check("T14-summary-confirms-test-not-loaded", not summary["test_loaded"])

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
print()
n_pass = sum(1 for _, ok in results if ok)
n_fail = sum(1 for _, ok in results if not ok)
print(f"Phase 4 Tests: {n_pass}/{len(results)} PASS  {n_fail} FAIL")

if n_fail > 0:
    print("\nFailed tests:")
    for name, ok in results:
        if not ok:
            print(f"  {FAIL} {name}")
    sys.exit(1)
else:
    print("All Phase 4 tests PASSED.")
    sys.exit(0)
