"""
Phase 8 — CMS Re-extraction, Retrain, and Final Evaluation
============================================================
Runs all three steps in sequence:
  1. Re-extract features for all 17,870 files with CMS enabled
  2. Retrain RF (same best config from Phase 5) on CMS features
  3. Evaluate on held-out test set — report full metrics
  4. Save final model artefacts

Rules
-----
- CMS (cms=True) is the only change to the extractor.
- Feature schema (124 features, same names) is unchanged.
- Model config: n_estimators=200, max_depth=20, min_samples_leaf=2 (Phase 5 best).
- Scaler refit on CMS train features only.
- Outputs saved to models/cms/ subdirectory to keep Phase 4/5 artefacts intact.
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
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
FEATURES_DIR = ROOT / "features"
MODELS_DIR = ROOT / "models" / "cms"
METADATA_DIR = ROOT / "metadata"
MANIFEST_CSV = METADATA_DIR / "acquisition_manifest.csv"
SPLIT_JSON = METADATA_DIR / "split_A_standard.json"

MODELS_DIR.mkdir(parents=True, exist_ok=True)

LABEL_MAP = {"FAKE": 1, "REAL": 0}
SPLIT_MAP = {"train": "training", "val": "validation", "test": "testing"}

# Phase 5 best RF config
RF_PARAMS = dict(
    n_estimators=200,
    max_depth=20,
    min_samples_leaf=2,
    max_features="sqrt",
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)


def compute_metrics(y_true, y_pred, y_prob, split_name: str) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    n_fake, n_real = tp + fn, tn + fp
    fnr = fn / n_fake if n_fake > 0 else 0.0
    fpr = fp / n_real if n_real > 0 else 0.0
    return {
        "split": split_name,
        "n_samples": int(len(y_true)),
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
    print(f"  [{label}] {m['split'].upper():<12} accuracy={m['accuracy']:.4f}"
          f"  FNR={m['fnr']:.4f}  FPR={m['fpr']:.4f}  ROC-AUC={m['roc_auc']:.4f}")
    cm = m["confusion_matrix"]
    print(f"              CM: TN={cm['tn']} FP={cm['fp']} FN={cm['fn']} TP={cm['tp']}")


def main():
    print("=" * 64)
    print("ADIS Phase 8 -- CMS Re-extraction + Retrain + Final Eval")
    print("=" * 64)

    # ------------------------------------------------------------------
    # 1. Load manifest + split JSON
    # ------------------------------------------------------------------
    print("\n[1/5] Loading manifest and split ...")
    df_manifest = pd.read_csv(MANIFEST_CSV)
    with open(SPLIT_JSON) as f:
        split_json = json.load(f)
    with open(METADATA_DIR / "feature_schema.json") as f:
        schema = json.load(f)
    feature_names: list[str] = schema["feature_names"]
    assert len(feature_names) == 124

    # Build id → row lookup
    id_to_row = {row["file_id"]: row for _, row in df_manifest.iterrows()}

    train_ids = split_json["train_ids"]
    val_ids   = split_json["val_ids"]
    test_ids  = split_json["test_ids"]
    print(f"      train={len(train_ids)}  val={len(val_ids)}  test={len(test_ids)}")

    # ------------------------------------------------------------------
    # 2. Re-extract features with CMS
    # ------------------------------------------------------------------
    sys.path.insert(0, str(ROOT))
    from features.extractor import extract_features

    def extract_split(ids: list[str], split_name: str) -> pd.DataFrame:
        rows = []
        n = len(ids)
        t0 = time.perf_counter()
        failures = 0
        for i, fid in enumerate(ids):
            if i % 2000 == 0:
                print(f"    [{split_name}] {i}/{n} ...")
            row = id_to_row[fid]
            feat, err = extract_features(row["path"], cms=True)
            if feat is None:
                failures += 1
                continue
            record = {"file_id": fid, "split": split_name, "label": row["label"]}
            for k in feature_names:
                record[k] = feat.get(k, 0.0)
            rows.append(record)
        elapsed = time.perf_counter() - t0
        print(f"    [{split_name}] done: {len(rows)}/{n} ok, {failures} failures, {elapsed:.0f}s")
        return pd.DataFrame(rows)

    print("\n[2/5] Re-extracting features with CMS ...")
    df_train_cms = extract_split(train_ids, "train")
    df_val_cms   = extract_split(val_ids,   "validation")
    df_test_cms  = extract_split(test_ids,  "test")

    # Save CMS CSVs
    df_train_cms.to_csv(FEATURES_DIR / "train_features_cms.csv", index=False)
    df_val_cms.to_csv(FEATURES_DIR / "validation_features_cms.csv", index=False)
    df_test_cms.to_csv(FEATURES_DIR / "test_features_cms.csv", index=False)
    print(f"      Saved CMS feature CSVs to {FEATURES_DIR}")

    # Build numpy arrays
    X_train = df_train_cms[feature_names].values.astype(np.float64)
    y_train = df_train_cms["label"].map(LABEL_MAP).values
    X_val   = df_val_cms[feature_names].values.astype(np.float64)
    y_val   = df_val_cms["label"].map(LABEL_MAP).values
    X_test  = df_test_cms[feature_names].values.astype(np.float64)
    y_test  = df_test_cms["label"].map(LABEL_MAP).values

    for name, X in [("train", X_train), ("val", X_val), ("test", X_test)]:
        assert not (np.any(np.isnan(X)) or np.any(np.isinf(X))), f"NaN/Inf in {name}"

    # ------------------------------------------------------------------
    # 3. Fit scaler on X_train, retrain RF
    # ------------------------------------------------------------------
    print("\n[3/5] Fitting scaler + retraining RF ...")
    scaler = StandardScaler()
    scaler.fit(X_train)

    t0 = time.perf_counter()
    rf = RandomForestClassifier(**RF_PARAMS)
    rf.fit(X_train, y_train)
    train_time = time.perf_counter() - t0
    print(f"      RF trained in {train_time:.1f}s")

    # ------------------------------------------------------------------
    # 4. Evaluate on val + test
    # ------------------------------------------------------------------
    print("\n[4/5] Evaluating ...")

    def eval_split(X, y, split_name):
        prob = rf.predict_proba(X)[:, 1]
        pred = (prob >= 0.5).astype(int)
        return compute_metrics(y, pred, prob, split_name)

    m_train = eval_split(X_train, y_train, "train")
    m_val   = eval_split(X_val,   y_val,   "validation")
    m_test  = eval_split(X_test,  y_test,  "test")

    print()
    print_metrics("RF-CMS", m_train)
    print_metrics("RF-CMS", m_val)
    print_metrics("RF-CMS", m_test)

    # ------------------------------------------------------------------
    # 5. Save artefacts
    # ------------------------------------------------------------------
    print("\n[5/5] Saving artefacts ...")
    joblib.dump(rf,     MODELS_DIR / "random_forest.joblib")
    joblib.dump(scaler, MODELS_DIR / "scaler.joblib")

    summary = {
        "phase": "Phase 8 -- CMS Re-extraction + Retrain + Final Eval",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "cms_applied": True,
        "cms_description": "Utterance-level Cepstral Mean Subtraction on MFCC rows before stat extraction",
        "rf_params": RF_PARAMS,
        "train_time_s": round(train_time, 2),
        "metrics_train": m_train,
        "metrics_val": m_val,
        "metrics_test": m_test,
        "val_test_fnr_gap": round(abs(m_val["fnr"] - m_test["fnr"]), 6),
        "val_test_accuracy_gap": round(abs(m_val["accuracy"] - m_test["accuracy"]), 6),
        "feature_names": feature_names,
        "notes": [
            "CMS neutralises codec artefacts (MP3 vs WAV confound in FOR-2sec).",
            "Scaler fit on CMS train features only.",
            "Test set loaded for final evaluation — no further model changes.",
        ],
    }
    with open(MODELS_DIR / "phase8_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"      Saved: {MODELS_DIR}/random_forest.joblib")
    print(f"      Saved: {MODELS_DIR}/scaler.joblib")
    print(f"      Saved: {MODELS_DIR}/phase8_summary.json")

    # ------------------------------------------------------------------
    # STOP report
    # ------------------------------------------------------------------
    print("\n" + "=" * 64)
    print("PHASE 8 COMPLETE -- STOP REPORT")
    print("=" * 64)
    print(f"\n  {'Split':<12}  {'Accuracy':>9}  {'FNR':>7}  {'FPR':>7}  {'ROC-AUC':>8}")
    print(f"  {'-'*12}  {'-'*9}  {'-'*7}  {'-'*7}  {'-'*8}")
    for m in [m_train, m_val, m_test]:
        print(f"  {m['split']:<12}  {m['accuracy']:>9.4f}  {m['fnr']:>7.4f}"
              f"  {m['fpr']:>7.4f}  {m['roc_auc']:>8.4f}")

    print(f"\n  Val/Test accuracy gap : {summary['val_test_accuracy_gap']:.4f}")
    print(f"  Val/Test FNR gap      : {summary['val_test_fnr_gap']:.4f}")

    if m_test["roc_auc"] >= 0.80:
        print("\n  [OK] Test ROC-AUC >= 0.80 -- CMS remediation SUCCESSFUL")
        print("  Ready for Phase 9 (ADIS integration) upon user approval.")
    else:
        print(f"\n  [WARN] Test ROC-AUC = {m_test['roc_auc']:.4f} -- below 0.80 threshold")
        print("  Further remediation needed before Phase 9.")

    print("=" * 64)


if __name__ == "__main__":
    main()
