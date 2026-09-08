"""
Phase 6 tests — verify test evaluation ran correctly and findings are documented.

Run:
    cd dist/backend
    .venv311/Scripts/python.exe services/audio_custom/train/phase6_tests.py
"""

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
MODELS_DIR = ROOT / "models"

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    msg = f"{status} {name}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results.append((name, condition))


# Load evaluation
try:
    with open(MODELS_DIR / "test_evaluation.json") as f:
        ev = json.load(f)
except FileNotFoundError:
    print(f"{FAIL} FATAL: test_evaluation.json not found")
    sys.exit(1)

# T01: File structure
for key in ["phase", "test_loaded", "positive_class", "primary_metric",
            "random_forest", "logistic_regression", "gemini_diagnostic", "notes"]:
    check(f"T01-has-{key}", key in ev)

# T02: Test was loaded (this file records it happened)
check("T02-test-loaded-flag", ev["test_loaded"] is True)

# T03: Test set size correct (1088 = 544 FAKE + 544 REAL)
ts = ev["test_set"]
check("T03-test-n-samples", ts["n_samples"] == 1088, f"n={ts['n_samples']}")
check("T03-test-n-fake", ts["n_fake"] == 544, f"n_fake={ts['n_fake']}")
check("T03-test-n-real", ts["n_real"] == 544, f"n_real={ts['n_real']}")

# T04: RF test metrics are present and structurally correct
rf_test = ev["random_forest"]["metrics_test"]
for k in ["accuracy", "precision", "recall", "f1", "roc_auc", "fpr", "fnr", "confusion_matrix"]:
    check(f"T04-rf-test-has-{k}", k in rf_test)

# T05: RF confusion matrix sums to 1088
cm = rf_test["confusion_matrix"]
total = cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"]
check("T05-rf-cm-total", total == 1088, f"total={total}")

# T06: LR test metrics present
lr_test = ev["logistic_regression"]["metrics_test"]
for k in ["accuracy", "fnr", "fpr", "roc_auc"]:
    check(f"T06-lr-test-has-{k}", k in lr_test)

# T07: Threshold sweep on test has 17 entries
n_thresh = len(ev["random_forest"]["threshold_sweep_test"])
check("T07-threshold-sweep-count", n_thresh == 17, f"n={n_thresh}")

# T08: Generalization gap is documented (we just verify metrics are recorded, not their values)
rf_val = ev["random_forest"]["metrics_val"]
check("T08-rf-val-metrics-present", "fnr" in rf_val and "accuracy" in rf_val)

# T09: Gemini result has a status field
gd = ev["gemini_diagnostic"]
check("T09-gemini-has-status", "status" in gd)
check("T09-gemini-status-valid", gd["status"] in ("EVALUATED", "PENDING", "ERROR"),
      f"status={gd['status']}")

# T10: Notes present and non-empty
check("T10-notes-present", isinstance(ev["notes"], list) and len(ev["notes"]) >= 3)

# T11: Model params recorded
rf_params = ev["random_forest"]["model_params"]
check("T11-rf-params-n-estimators", "n_estimators" in rf_params)
check("T11-rf-params-max-depth", "max_depth" in rf_params)

# T12: Inference time recorded
check("T12-inference-time-recorded",
      "inference_time_ms_total" in ev["random_forest"])

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
print()
n_pass = sum(1 for _, ok in results if ok)
n_fail = sum(1 for _, ok in results if not ok)
print(f"Phase 6 Tests: {n_pass}/{len(results)} PASS  {n_fail} FAIL")

if n_fail > 0:
    print("\nFailed tests:")
    for name, ok in results:
        if not ok:
            print(f"  {FAIL} {name}")
    sys.exit(1)
else:
    print("All Phase 6 tests PASSED.")
    sys.exit(0)
