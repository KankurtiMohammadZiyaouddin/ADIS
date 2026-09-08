"""
Phase 6 — Final Held-Out Test Evaluation
==========================================
THIS IS THE ONLY SCRIPT THAT LOADS test_features.csv.
It must be run exactly ONCE — after Phase 5 is complete and approved.

Rules
-----
- No model changes after seeing test results (that would be leakage).
- Scaler and models are loaded from disk — never refit here.
- FAKE=1 (positive class), REAL=0.
- Primary metric: FNR (FAKE predicted as REAL).
- Gemini diagnostic is run if the file exists in tests/unseen_gemini/.
  If absent, it is logged as PENDING — not an error.
- All results saved to models/test_evaluation.json.

Outputs (models/)
-----------------
  test_evaluation.json    complete final results
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
FEATURES_DIR = ROOT / "features"
MODELS_DIR = ROOT / "models"
METADATA_DIR = ROOT / "metadata"
GEMINI_DIR = ROOT / "tests" / "unseen_gemini"

TEST_CSV = FEATURES_DIR / "test_features.csv"
SCHEMA_JSON = METADATA_DIR / "feature_schema.json"

LABEL_MAP = {"FAKE": 1, "REAL": 0}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compute_metrics(y_true, y_pred, y_prob, split_name: str) -> dict:
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
        "confusion_matrix": {
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        },
    }


def print_metrics(label: str, m: dict) -> None:
    print(f"\n  [{label}] {m['split'].upper()} -- n={m['n_samples']}")
    print(f"    Accuracy  : {m['accuracy']:.4f}")
    print(f"    Precision : {m['precision']:.4f}  Recall: {m['recall']:.4f}  F1: {m['f1']:.4f}")
    print(f"    ROC-AUC   : {m['roc_auc']:.4f}")
    print(f"    FPR       : {m['fpr']:.4f}  FNR (primary): {m['fnr']:.4f}")
    cm = m["confusion_matrix"]
    print(f"    Confusion  : TN={cm['tn']} FP={cm['fp']} FN={cm['fn']} TP={cm['tp']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 64)
    print("ADIS Phase 6 -- Final Held-Out Test Evaluation")
    print("=" * 64)
    print("  WARNING: Test set is being loaded. No model changes permitted after this.")

    # ------------------------------------------------------------------
    # 1. Load schema + models
    # ------------------------------------------------------------------
    with open(SCHEMA_JSON) as f:
        schema = json.load(f)
    feature_names = schema["feature_names"]
    assert len(feature_names) == 124

    print("\n[1/5] Loading models ...")
    scaler = joblib.load(MODELS_DIR / "scaler.joblib")
    lr = joblib.load(MODELS_DIR / "logistic_regression.joblib")
    rf = joblib.load(MODELS_DIR / "random_forest.joblib")
    print(f"      RF  : n_estimators={rf.n_estimators}  max_depth={rf.max_depth}"
          f"  min_leaf={rf.min_samples_leaf}")
    print(f"      LR  : C={lr.C}")
    print(f"      Scaler: mean_.shape={scaler.mean_.shape}")

    # ------------------------------------------------------------------
    # 2. Load test set (first and only time)
    # ------------------------------------------------------------------
    print("\n[2/5] Loading test set ...")
    df_test = pd.read_csv(TEST_CSV)
    X_test = df_test[feature_names].values.astype(np.float64)
    y_test = df_test["label"].map(LABEL_MAP).values
    assert not (np.any(np.isnan(X_test)) or np.any(np.isinf(X_test))), "NaN/Inf in test set"
    print(f"      Test: {X_test.shape}  FAKE={y_test.sum()}  REAL={(y_test==0).sum()}")

    X_test_scaled = scaler.transform(X_test)

    # Also load val for side-by-side comparison
    df_val = pd.read_csv(FEATURES_DIR / "validation_features.csv")
    X_val = df_val[feature_names].values.astype(np.float64)
    y_val = df_val["label"].map(LABEL_MAP).values
    X_val_scaled = scaler.transform(X_val)

    # ------------------------------------------------------------------
    # 3. Evaluate RF
    # ------------------------------------------------------------------
    print("\n[3/5] Evaluating Random Forest ...")
    t0 = time.perf_counter()
    rf_test_prob = rf.predict_proba(X_test)[:, 1]
    rf_test_pred = (rf_test_prob >= 0.5).astype(int)
    rf_test_time = time.perf_counter() - t0

    rf_val_prob = rf.predict_proba(X_val)[:, 1]
    rf_val_pred = (rf_val_prob >= 0.5).astype(int)

    rf_m_val = compute_metrics(y_val, rf_val_pred, rf_val_prob, "validation")
    rf_m_test = compute_metrics(y_test, rf_test_pred, rf_test_prob, "test")

    print_metrics("RF", rf_m_val)
    print_metrics("RF", rf_m_test)
    print(f"\n  RF inference time on test: {rf_test_time*1000:.1f}ms  "
          f"({rf_test_time/len(y_test)*1000:.3f}ms/sample)")

    # Threshold sweep on test for reference (not for model selection)
    print("\n  RF threshold sweep on TEST (reference only -- not for model selection):")
    print(f"  {'Threshold':>10} {'Accuracy':>10} {'FNR':>8} {'FPR':>8}")
    print(f"  {'-'*10} {'-'*10} {'-'*8} {'-'*8}")
    thresh_test_results = []
    for t in np.arange(0.10, 0.91, 0.05):
        y_pred_t = (rf_test_prob >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred_t, labels=[0, 1]).ravel()
        n_fake = tp + fn
        n_real = tn + fp
        fnr_t = fn / n_fake if n_fake > 0 else 0.0
        fpr_t = fp / n_real if n_real > 0 else 0.0
        acc_t = (tp + tn) / len(y_test)
        entry = {
            "threshold": round(float(t), 2),
            "accuracy": round(float(acc_t), 6),
            "fnr": round(float(fnr_t), 6),
            "fpr": round(float(fpr_t), 6),
        }
        thresh_test_results.append(entry)
        marker = " <-- default" if abs(t - 0.50) < 0.01 else ""
        print(f"  {t:>10.2f} {acc_t:>10.4f} {fnr_t:>8.4f} {fpr_t:>8.4f}{marker}")

    # ------------------------------------------------------------------
    # 4. Evaluate LR
    # ------------------------------------------------------------------
    print("\n[4/5] Evaluating Logistic Regression ...")
    t0 = time.perf_counter()
    lr_test_prob = lr.predict_proba(X_test_scaled)[:, 1]
    lr_test_pred = (lr_test_prob >= 0.5).astype(int)
    lr_test_time = time.perf_counter() - t0

    lr_val_prob = lr.predict_proba(X_val_scaled)[:, 1]
    lr_val_pred = (lr_val_prob >= 0.5).astype(int)

    lr_m_val = compute_metrics(y_val, lr_val_pred, lr_val_prob, "validation")
    lr_m_test = compute_metrics(y_test, lr_test_pred, lr_test_prob, "test")

    print_metrics("LR", lr_m_val)
    print_metrics("LR", lr_m_test)

    # ------------------------------------------------------------------
    # 5. Gemini diagnostic (unseen generator)
    # ------------------------------------------------------------------
    print("\n[5/5] Gemini unseen-generator diagnostic ...")

    # Import extractor
    extractor_path = ROOT / "features"
    sys.path.insert(0, str(ROOT))
    gemini_result = None

    gemini_files = list(GEMINI_DIR.glob("*.mp3")) + list(GEMINI_DIR.glob("*.wav")) + \
                   list(GEMINI_DIR.glob("*.m4a")) + list(GEMINI_DIR.glob("*.flac"))

    if not gemini_files:
        print("  Gemini file NOT found in tests/unseen_gemini/ -- PENDING")
        gemini_result = {
            "status": "PENDING",
            "reason": "No audio file found in tests/unseen_gemini/",
            "note": "Place a_simple_boy_infront_of_the_oc.mp3 there and rerun for diagnostic.",
        }
    else:
        try:
            from features.extractor import extract_features
            from features.schema import build_feature_names

            gemini_file = gemini_files[0]
            print(f"  Found: {gemini_file.name}")

            raw_features = extract_features(str(gemini_file))
            expected_names = build_feature_names()
            x_gemini = np.array([[raw_features[k] for k in expected_names]], dtype=np.float64)

            rf_prob_g = rf.predict_proba(x_gemini)[0, 1]
            rf_pred_g = int(rf_prob_g >= 0.5)
            rf_label_g = "FAKE" if rf_pred_g == 1 else "REAL"

            lr_prob_g = lr.predict_proba(scaler.transform(x_gemini))[0, 1]
            lr_pred_g = int(lr_prob_g >= 0.5)
            lr_label_g = "FAKE" if lr_pred_g == 1 else "REAL"

            print(f"  RF  : p(FAKE)={rf_prob_g:.4f}  prediction={rf_label_g}")
            print(f"  LR  : p(FAKE)={lr_prob_g:.4f}  prediction={lr_label_g}")
            print("  NOTE: Preliminary unseen-generator result. No ground truth available.")
            print("  NOTE: Gemini was NEVER used for training, tuning, or feature selection.")

            gemini_result = {
                "status": "EVALUATED",
                "file": gemini_file.name,
                "disclaimer": "Preliminary unseen-generator result — no ground truth available.",
                "leakage_note": "Gemini file never used in training, tuning, or feature selection.",
                "rf": {"p_fake": round(float(rf_prob_g), 6), "prediction": rf_label_g},
                "lr": {"p_fake": round(float(lr_prob_g), 6), "prediction": lr_label_g},
            }
        except Exception as e:
            print(f"  ERROR during Gemini extraction: {e}")
            gemini_result = {"status": "ERROR", "error": str(e)}

    # ------------------------------------------------------------------
    # Save test_evaluation.json
    # ------------------------------------------------------------------
    evaluation = {
        "phase": "Phase 6 -- Final Held-Out Test Evaluation",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "test_loaded": True,
        "positive_class": "FAKE",
        "primary_metric": "FNR (FAKE classified as REAL)",
        "dataset": "FOR-2sec (for-2seconds)",
        "test_set": {
            "n_samples": int(len(y_test)),
            "n_fake": int(y_test.sum()),
            "n_real": int((y_test == 0).sum()),
            "source": "test_features.csv (official FOR-2sec test split)",
        },
        "random_forest": {
            "model_params": {
                "n_estimators": rf.n_estimators,
                "max_depth": rf.max_depth,
                "min_samples_leaf": rf.min_samples_leaf,
                "max_features": rf.max_features,
            },
            "metrics_val": rf_m_val,
            "metrics_test": rf_m_test,
            "inference_time_ms_total": round(rf_test_time * 1000, 2),
            "inference_time_ms_per_sample": round(rf_test_time / len(y_test) * 1000, 4),
            "threshold_sweep_test": thresh_test_results,
        },
        "logistic_regression": {
            "model_params": {"C": lr.C},
            "metrics_val": lr_m_val,
            "metrics_test": lr_m_test,
        },
        "gemini_diagnostic": gemini_result,
        "notes": [
            "Test set loaded for the first and only time in Phase 6.",
            "No model changes are permitted after this evaluation.",
            "FNR is primary metric: FAKE predicted as REAL is the safety-critical error.",
            "FOR-2sec fake sources: Deep Voice 3 + Google WaveNet (same generators in all splits).",
            "Threshold sweep on test is for reference only — default=0.50 is the production threshold.",
        ],
    }

    eval_path = MODELS_DIR / "test_evaluation.json"
    with open(eval_path, "w") as f:
        json.dump(evaluation, f, indent=2)
    print(f"\n  Saved: {eval_path}")

    # ------------------------------------------------------------------
    # STOP report
    # ------------------------------------------------------------------
    print("\n" + "=" * 64)
    print("PHASE 6 COMPLETE -- STOP REPORT")
    print("=" * 64)

    print(f"\n  {'Model':<6}  {'Split':<12}  {'Accuracy':>9}  {'FNR':>7}  {'FPR':>7}  {'ROC-AUC':>8}")
    print(f"  {'-'*6}  {'-'*12}  {'-'*9}  {'-'*7}  {'-'*7}  {'-'*8}")
    for m, label in [(rf_m_val, "RF val"), (rf_m_test, "RF test"),
                     (lr_m_val, "LR val"), (lr_m_test, "LR test")]:
        print(f"  {label:<18}  {m['accuracy']:>9.4f}  {m['fnr']:>7.4f}  {m['fpr']:>7.4f}  {m['roc_auc']:>8.4f}")

    val_test_acc_gap_rf = abs(rf_m_val["accuracy"] - rf_m_test["accuracy"])
    val_test_fnr_gap_rf = abs(rf_m_val["fnr"] - rf_m_test["fnr"])
    print(f"\n  RF val/test accuracy gap : {val_test_acc_gap_rf:.4f}")
    print(f"  RF val/test FNR gap      : {val_test_fnr_gap_rf:.4f}")

    if gemini_result and gemini_result["status"] == "EVALUATED":
        print(f"\n  Gemini diagnostic: RF p(FAKE)={gemini_result['rf']['p_fake']:.4f}"
              f"  prediction={gemini_result['rf']['prediction']}")
    else:
        print(f"\n  Gemini diagnostic: {gemini_result['status']}")

    print("\n  Next: await user approval before Phase 7 (analysis + failure audit).")
    print("=" * 64)


if __name__ == "__main__":
    main()
