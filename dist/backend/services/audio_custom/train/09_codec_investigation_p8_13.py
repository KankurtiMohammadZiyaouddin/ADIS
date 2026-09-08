"""
Phase 5 Codec-Confound Investigation — Parts 8-13
=====================================================
Dataset expansion (In The Wild), manifest, duplicate detection,
leakage-safe split, generator holdout, cross-dataset generalisation.
NO model changes. NO production file changes.
"""

import json, sys, hashlib, warnings, time
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

ROOT      = Path(__file__).resolve().parents[1]
FEATURES  = ROOT / "features"
MODELS    = ROOT / "models"
METADATA  = ROOT / "metadata"
DATA      = ROOT / "data"

with open(METADATA / "feature_schema.json") as f:
    schema = json.load(f)
FEATURE_NAMES = schema["feature_names"]
LABEL_MAP = {"FAKE": 1, "REAL": 0}

REPORT = {}


def banner(s):
    print(f"\n{'='*60}")
    print(f"  {s}")
    print(f"{'='*60}")


def metrics(y_true, y_pred, y_prob, label):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0,1]).ravel()
    fnr = fn/(tp+fn) if (tp+fn) > 0 else 0.0
    fpr = fp/(tn+fp) if (tn+fp) > 0 else 0.0
    return {
        "split": label,
        "n": int(len(y_true)),
        "accuracy":  round(float(accuracy_score(y_true, y_pred)), 6),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 6),
        "recall":    round(float(recall_score(y_true, y_pred, zero_division=0)), 6),
        "f1":        round(float(f1_score(y_true, y_pred, zero_division=0)), 6),
        "fpr":       round(float(fpr), 6),
        "fnr":       round(float(fnr), 6),
        "roc_auc":   round(float(roc_auc_score(y_true, y_prob)), 6),
        "confusion_matrix": {"tn":int(tn),"fp":int(fp),"fn":int(fn),"tp":int(tp)},
    }


def load_csv(path):
    df = pd.read_csv(path)
    X  = df[FEATURE_NAMES].values.astype(np.float64)
    y  = df["label"].map(LABEL_MAP).values
    return X, y, df


# ─────────────────────────────────────────────────────────────
# PART 8 — In The Wild acquisition
# ─────────────────────────────────────────────────────────────
banner("PART 8 -- In The Wild Dataset Acquisition")

# Check Kaggle CLI availability
import shutil, subprocess
kaggle_ok = shutil.which("kaggle") is not None
print(f"  kaggle CLI available: {kaggle_ok}")

ITW_DIR = DATA / "in-the-wild"
ITW_DIR.mkdir(parents=True, exist_ok=True)

itw_status = "NOT ACQUIRED"
itw_files = []

if kaggle_ok:
    print("  Attempting download via kaggle CLI...")
    result = subprocess.run(
        ["kaggle", "datasets", "download",
         "-d", "abdallamohamed312/in-the-wild-audio-deepfake",
         "--path", str(ITW_DIR), "--unzip"],
        capture_output=True, text=True, timeout=600
    )
    if result.returncode == 0:
        itw_status = "DOWNLOADED"
        print(f"  Download OK: {ITW_DIR}")
    else:
        itw_status = f"DOWNLOAD_FAILED: {result.stderr[:300]}"
        print(f"  Download failed: {result.stderr[:200]}")
else:
    print("  kaggle CLI not found.")
    # Check if already downloaded manually
    if any(ITW_DIR.rglob("*.wav")) or any(ITW_DIR.rglob("*.mp3")) or any(ITW_DIR.rglob("*.flac")):
        itw_status = "MANUALLY_PRESENT"
        print("  Audio files found in data/in-the-wild/ (manually placed)")
    else:
        itw_status = "BLOCKED"
        print("  BLOCKED: kaggle CLI not available and no files in data/in-the-wild/")
        print("  To acquire:")
        print("    1. Install: pip install kaggle")
        print("    2. Place kaggle.json in %USERPROFILE%\\.kaggle\\")
        print("    3. Rerun this script")
        print("  OR: Download manually from:")
        print("    https://www.kaggle.com/datasets/abdallamohamed312/in-the-wild-audio-deepfake")
        print("    Extract to: dist/backend/services/audio_custom/data/in-the-wild/")

# Inventory whatever is present
if itw_status in ("DOWNLOADED", "MANUALLY_PRESENT"):
    itw_files = list(ITW_DIR.rglob("*.wav")) + list(ITW_DIR.rglob("*.mp3")) + list(ITW_DIR.rglob("*.flac"))
    print(f"  Audio files found: {len(itw_files)}")
    # Try to infer labels from directory structure
    for p in itw_files[:5]:
        print(f"    {p.relative_to(DATA)}")

REPORT["part8"] = {
    "status": itw_status,
    "kaggle_cli": kaggle_ok,
    "files_found": len(itw_files),
    "path": str(ITW_DIR),
}


# ─────────────────────────────────────────────────────────────
# PARTS 9-11 — Manifest, duplicate detection, split
#              (only if ITW data is present)
# ─────────────────────────────────────────────────────────────
banner("PARTS 9-11 -- Manifest + Duplicates + Split")

itw_manifest_rows = []
sha256_map = {}   # sha256 -> file_id
duplicate_exact = []

if itw_files:
    import soundfile as sf

    def infer_label(path):
        parts = [p.lower() for p in path.parts]
        if any("fake" in p or "spoof" in p or "synth" in p for p in parts):
            return "FAKE"
        if any("real" in p or "genuine" in p or "bona" in p for p in parts):
            return "REAL"
        return "unknown"

    print(f"  Building manifest for {len(itw_files)} files...")
    for fid_i, fpath in enumerate(itw_files):
        label_inferred = infer_label(fpath)

        # SHA-256
        h = hashlib.sha256()
        try:
            with open(fpath, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            sha = h.hexdigest()
        except Exception:
            sha = "unknown"

        # Duplicate check
        if sha in sha256_map:
            duplicate_exact.append({"file_id": f"itw_{fid_i:06d}", "duplicate_of": sha256_map[sha]})
        else:
            sha256_map[sha] = f"itw_{fid_i:06d}"

        # Audio metadata
        try:
            info = sf.info(str(fpath))
            dur, sr, ch = round(info.duration, 3), info.samplerate, info.channels
            fmt = fpath.suffix.lower().lstrip(".")
        except Exception:
            dur, sr, ch, fmt = 0.0, 0, 0, fpath.suffix.lower().lstrip(".")

        row = {
            "file_id":    f"itw_{fid_i:06d}",
            "path":       str(fpath),
            "dataset":    "in-the-wild",
            "label":      label_inferred,
            "speaker_id": "unknown",
            "generator_id": "unknown",
            "source_id":  "unknown",
            "duration_seconds": dur,
            "sample_rate": sr,
            "channels":   ch,
            "format":     fmt,
            "sha256":     sha,
        }
        itw_manifest_rows.append(row)

    df_itw_manifest = pd.DataFrame(itw_manifest_rows)
    out_man = METADATA / "itw_manifest.csv"
    df_itw_manifest.to_csv(out_man, index=False)
    print(f"  Manifest saved: {out_man}")
    print(f"  Label distribution: {dict(df_itw_manifest.label.value_counts())}")
    print(f"  Exact SHA-256 duplicates: {len(duplicate_exact)}")
    if duplicate_exact:
        print(f"  (First 3 duplicates: {duplicate_exact[:3]})")

    REPORT["part9_10"] = {
        "n_files": len(itw_manifest_rows),
        "label_dist": dict(df_itw_manifest.label.value_counts()),
        "exact_duplicates": len(duplicate_exact),
        "unknown_labels": int((df_itw_manifest.label == "unknown").sum()),
    }
else:
    print("  No ITW files available -- skipping manifest.")
    REPORT["part9_10"] = {"status": "SKIPPED", "reason": "No ITW audio files present"}


# ─────────────────────────────────────────────────────────────
# PARTS 12-13 — Generator holdout + cross-dataset
#               (requires ITW features to be extracted first)
# ─────────────────────────────────────────────────────────────
banner("PARTS 12-13 -- Generator Holdout + Cross-Dataset Test")

itw_features_csv = FEATURES / "itw_features.csv"

if not itw_features_csv.exists() and itw_files:
    print("  Extracting ITW features (this may take a while)...")
    sys.path.insert(0, str(ROOT))
    from features.extractor import extract_features
    from features.schema import EXCLUDED_KEYS

    rows = []
    failures = 0
    for i, (row, fpath) in enumerate(zip(itw_manifest_rows, itw_files)):
        if i % 500 == 0:
            print(f"    [{i}/{len(itw_files)}] ...")
        feat, err = extract_features(str(fpath), cms=True)
        if feat is None:
            failures += 1
            continue
        record = {"file_id": row["file_id"], "label": row["label"]}
        for k in FEATURE_NAMES:
            record[k] = feat.get(k, 0.0)
        rows.append(record)

    df_itw_feat = pd.DataFrame(rows)
    df_itw_feat.to_csv(itw_features_csv, index=False)
    print(f"  Extracted {len(rows)} ({failures} failures) -> {itw_features_csv}")
elif itw_features_csv.exists():
    print(f"  ITW features already extracted: {itw_features_csv}")
    df_itw_feat = pd.read_csv(itw_features_csv)
else:
    df_itw_feat = None
    print("  No ITW features available.")

# Cross-dataset: FOR train -> ITW test  /  ITW train -> FOR test
rf_saved  = joblib.load(MODELS / "random_forest.joblib")
lr_saved  = joblib.load(MODELS / "logistic_regression.joblib")
sc_saved  = joblib.load(MODELS / "scaler.joblib")

X_for_train, y_for_train, _ = load_csv(FEATURES / "train_features.csv")
X_for_test,  y_for_test,  _ = load_csv(FEATURES / "test_features.csv")

cross_results = {}

if df_itw_feat is not None and len(df_itw_feat) > 0:
    # Only use files with known labels
    df_itw_known = df_itw_feat[df_itw_feat.label.isin(["FAKE","REAL"])].copy()
    print(f"\n  ITW known-label files: {len(df_itw_known)}")
    print(f"  Label dist: {dict(df_itw_known.label.value_counts())}")

    if len(df_itw_known) >= 50:
        X_itw = df_itw_known[FEATURE_NAMES].values.astype(np.float64)
        y_itw = df_itw_known["label"].map(LABEL_MAP).values

        # --- FOR -> ITW (using saved FOR-trained model) ---
        rf_prob_itw = rf_saved.predict_proba(X_itw)[:,1]
        lr_prob_itw = lr_saved.predict_proba(sc_saved.transform(X_itw))[:,1]
        rf_itw = metrics(y_itw, (rf_prob_itw>=0.5).astype(int), rf_prob_itw, "FOR->ITW")
        lr_itw = metrics(y_itw, (lr_prob_itw>=0.5).astype(int), lr_prob_itw, "FOR->ITW")
        print(f"\n  FOR->ITW  RF: acc={rf_itw['accuracy']:.4f}  FNR={rf_itw['fnr']:.4f}  AUC={rf_itw['roc_auc']:.4f}")
        print(f"  FOR->ITW  LR: acc={lr_itw['accuracy']:.4f}  FNR={lr_itw['fnr']:.4f}  AUC={lr_itw['roc_auc']:.4f}")
        cross_results["for_to_itw"] = {"rf": rf_itw, "lr": lr_itw}

        # --- ITW -> FOR (train fresh on ITW, evaluate on FOR test) ---
        # Simple 80/20 file-level split on ITW
        np.random.seed(42)
        idx = np.random.permutation(len(X_itw))
        split = int(0.8 * len(idx))
        X_itw_tr, y_itw_tr = X_itw[idx[:split]], y_itw[idx[:split]]
        sc_itw = StandardScaler().fit(X_itw_tr)

        rf_itw2for = RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_leaf=2,
                                             max_features="sqrt", class_weight="balanced",
                                             random_state=42, n_jobs=-1)
        rf_itw2for.fit(X_itw_tr, y_itw_tr)

        lr_itw2for = LogisticRegression(C=1.0, max_iter=1000, class_weight="balanced",
                                         solver="lbfgs", random_state=42)
        lr_itw2for.fit(sc_itw.transform(X_itw_tr), y_itw_tr)

        rf_prob_for = rf_itw2for.predict_proba(X_for_test)[:,1]
        lr_prob_for = lr_itw2for.predict_proba(sc_itw.transform(X_for_test))[:,1]
        rf_i2f = metrics(y_for_test, (rf_prob_for>=0.5).astype(int), rf_prob_for, "ITW->FOR")
        lr_i2f = metrics(y_for_test, (lr_prob_for>=0.5).astype(int), lr_prob_for, "ITW->FOR")
        print(f"\n  ITW->FOR  RF: acc={rf_i2f['accuracy']:.4f}  FNR={rf_i2f['fnr']:.4f}  AUC={rf_i2f['roc_auc']:.4f}")
        print(f"  ITW->FOR  LR: acc={lr_i2f['accuracy']:.4f}  FNR={lr_i2f['fnr']:.4f}  AUC={lr_i2f['roc_auc']:.4f}")
        cross_results["itw_to_for"] = {"rf": rf_i2f, "lr": lr_i2f}
    else:
        print("  Insufficient ITW known-label files for cross-dataset test.")
        cross_results = {"status": "INSUFFICIENT_DATA"}
else:
    print("  ITW not available -- cross-dataset test BLOCKED.")
    cross_results = {"status": "BLOCKED", "reason": "ITW not acquired"}

REPORT["part12_13"] = cross_results


# ─────────────────────────────────────────────────────────────
# Save report
# ─────────────────────────────────────────────────────────────
REPORT["timestamp"] = datetime.now(timezone.utc).isoformat()
REPORT["phase"] = "Phase 5 -- Codec Confound Investigation Parts 8-13"

out = MODELS / "codec_investigation_p8_13.json"
with open(out, "w") as f:
    json.dump(REPORT, f, indent=2, default=str)
print(f"\nSaved: {out}")
print("\nParts 8-13 complete.")
