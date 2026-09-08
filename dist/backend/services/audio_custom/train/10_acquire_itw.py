"""
ITW Acquisition + Feature Extraction + Cross-Dataset Evaluation
================================================================
Run AFTER kaggle credentials are configured.

NEW API auth (kaggle >= 1.7): run once in any shell:
    kaggle auth login          (OAuth browser flow)
OR place a kaggle.json at:
    C:\\Users\\<you>\\.kaggle\\kaggle.json
    with content: {"username":"...", "key":"..."}

Then run from the audio_custom/train/ directory:
    ..\\..\\..\\..\\..\\..\\dist\\backend\\.venv311\\Scripts\\python.exe 10_acquire_itw.py

Confirmed dataset slug: abdallamohamed312/in-the-wild-dataset
"""

# ── Standard library ──────────────────────────────────────────────────────────
import subprocess, shutil, json, hashlib, sys, warnings, os
from pathlib import Path

# ── Third-party (all imported at top so failures surface immediately) ─────────
import numpy as np
import pandas as pd
import joblib
import soundfile as sf
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, confusion_matrix, accuracy_score,
    f1_score, precision_score, recall_score,
)
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "features"
MODELS   = ROOT / "models"
METADATA = ROOT / "metadata"
DATA_ITW = ROOT / "data" / "in-the-wild"
DATA_ITW.mkdir(parents=True, exist_ok=True)

# ── Load feature schema ───────────────────────────────────────────────────────
with open(METADATA / "feature_schema.json") as f:
    FEATURE_NAMES = json.load(f)["feature_names"]
LABEL_MAP = {"FAKE": 1, "REAL": 0}

# ── Locate Kaggle CLI  ────────────────────────────────────────────────────────
# Priority order:
#   1. KAGGLE_CLI env var (explicit override)
#   2. venv311 Scripts directory (co-located, always checked first)
#   3. shutil.which (system PATH)
#   4. Python 3.14 user Scripts (known working location on this machine)
_CANDIDATE_KAGGLE_PATHS = [
    os.environ.get("KAGGLE_CLI", ""),
    str(ROOT.parents[3] / ".venv311" / "Scripts" / "kaggle.exe"),   # dist/backend/.venv311
    shutil.which("kaggle") or "",
    r"C:\Users\ZIYAOUDDIN\AppData\Roaming\Python\Python314\Scripts\kaggle.exe",
]
kaggle_cli = next(
    (p for p in _CANDIDATE_KAGGLE_PATHS if p and Path(p).is_file()),
    None,
)
if kaggle_cli is None:
    print("ERROR: kaggle CLI not found. Install with: pip install kaggle")
    print("       Then authenticate: kaggle auth login")
    sys.exit(1)
print(f"Using kaggle CLI: {kaggle_cli}")

# Quick auth probe — if it fails, print clear instructions and exit early
# (avoids wasting time starting the download with bad credentials)
_probe = subprocess.run(
    [kaggle_cli, "datasets", "list", "--search", "in-the-wild", "--max-size", "1"],
    capture_output=True, text=True, timeout=30,
)
if _probe.returncode != 0 or "Authentication" in (_probe.stderr + _probe.stdout):
    print("ERROR: Kaggle authentication required.")
    print("  Option A — OAuth (browser): kaggle auth login")
    print("  Option B — API token file:  place kaggle.json at ~/.kaggle/kaggle.json")
    print("             Content: {\"username\":\"...\", \"key\":\"...\"}")
    print("  After authenticating, re-run this script.")
    sys.exit(1)
print("Kaggle auth OK.")

# ── Correct dataset slug (verified via Kaggle API in previous session) ────────
ITW_SLUG = "abdallamohamed312/in-the-wild-dataset"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Download
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[Step 1] Downloading {ITW_SLUG} ...")
r = subprocess.run(
    [kaggle_cli, "datasets", "download",
     "-d", ITW_SLUG,
     "--path", str(DATA_ITW), "--unzip"],
    capture_output=True, text=True, timeout=7200,   # 2-hour hard cap
)
if r.returncode != 0:
    print("DOWNLOAD FAILED:")
    print(r.stderr[:1000])
    sys.exit(1)
print("Download complete.")

# Show what was extracted — essential to verify ITW structure before label inference
print("\n[Step 1b] Extracted structure (top-2 levels):")
for item in sorted(DATA_ITW.rglob("*"))[:80]:
    if item.is_dir() or item.suffix.lower() in {".csv", ".txt", ".json", ".tsv"}:
        print(f"  {item.relative_to(DATA_ITW)}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Inventory audio files
# ─────────────────────────────────────────────────────────────────────────────
print("\n[Step 2] Scanning for audio files...")
audio_files = (
    list(DATA_ITW.rglob("*.wav")) +
    list(DATA_ITW.rglob("*.mp3")) +
    list(DATA_ITW.rglob("*.flac"))
)
print(f"Found {len(audio_files)} audio files")
if len(audio_files) == 0:
    print("ERROR: No audio files found. Check the extraction above for unexpected archive structure.")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Label inference
# ─────────────────────────────────────────────────────────────────────────────
# ITW dataset (Müller et al. 2022) ships a metadata CSV alongside the audio.
# The ground-truth label is in that CSV, NOT in directory names.
# Strategy:
#   1. If a metadata CSV exists in DATA_ITW, use it.
#   2. Otherwise fall back to directory-name heuristics and warn loudly.

def _load_itw_metadata_csv(root: Path) -> dict:
    """
    Search for the bundled metadata CSV and return a {filename: label} dict.
    ITW ships a file typically named 'meta.csv' or 'release_meta.csv' with
    columns including 'file' (or 'filename') and 'label' (or 'type').
    """
    candidates = sorted(root.rglob("*.csv"))
    print(f"  Candidate CSV files: {[str(c.relative_to(root)) for c in candidates]}")
    for csv_path in candidates:
        try:
            df = pd.read_csv(csv_path)
            cols = [c.lower() for c in df.columns]
            # Detect file column
            file_col = next((df.columns[i] for i, c in enumerate(cols)
                             if c in {"file", "filename", "path", "clip"}), None)
            # Detect label column
            label_col = next((df.columns[i] for i, c in enumerate(cols)
                              if c in {"label", "type", "target", "class", "deepfake"}), None)
            if file_col and label_col:
                print(f"  Using metadata CSV: {csv_path.relative_to(root)}")
                print(f"    file_col={file_col}, label_col={label_col}, rows={len(df)}")
                print(f"    label values: {df[label_col].value_counts().to_dict()}")
                # Build lookup: stem → label
                lookup = {}
                for _, row in df.iterrows():
                    raw_label = str(row[label_col]).strip().upper()
                    # Normalise to FAKE/REAL
                    if raw_label in {"FAKE", "SPOOF", "DEEPFAKE", "GENERATED", "SYNTHETIC",
                                     "1", "TRUE"}:
                        norm = "FAKE"
                    elif raw_label in {"REAL", "GENUINE", "BONA", "HUMAN", "ORIGINAL",
                                       "BONAFIDE", "0", "FALSE"}:
                        norm = "REAL"
                    else:
                        norm = "unknown"
                    key = Path(str(row[file_col])).stem.lower()
                    lookup[key] = norm
                return lookup
        except Exception as e:
            print(f"  Could not parse {csv_path}: {e}")
    return {}

print("\n[Step 3] Inferring labels...")
_itw_meta_lookup = _load_itw_metadata_csv(DATA_ITW)
if _itw_meta_lookup:
    print(f"  Metadata CSV loaded: {len(_itw_meta_lookup)} entries")
else:
    print("  WARNING: No metadata CSV found — falling back to directory-name heuristics.")
    print("  This may produce all-'unknown' labels if ITW uses non-keyword directory names.")

def infer_label(path: Path) -> str:
    # Priority 1: metadata CSV lookup by file stem
    stem = path.stem.lower()
    if stem in _itw_meta_lookup:
        return _itw_meta_lookup[stem]
    # Priority 2: directory-name keyword heuristic (fallback only)
    parts = [p.lower() for p in path.parts]
    if any(w in p for p in parts for w in ["fake", "spoof", "synth", "deepfake", "generated"]):
        return "FAKE"
    if any(w in p for p in parts for w in ["real", "genuine", "bona", "human", "original"]):
        return "REAL"
    return "unknown"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Build manifest with SHA-256
# ─────────────────────────────────────────────────────────────────────────────
print("\n[Step 4] Building manifest (SHA-256 + metadata)...")
rows, sha_seen = [], {}
for i, p in enumerate(audio_files):
    if i % 1000 == 0:
        print(f"  manifest [{i}/{len(audio_files)}]")
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    sha = h.hexdigest()
    dup_of = sha_seen.get(sha)
    sha_seen[sha] = f"itw_{i:06d}"
    try:
        info = sf.info(str(p))
        dur, sr, ch = round(info.duration, 3), info.samplerate, info.channels
    except Exception:
        dur, sr, ch = 0.0, 0, 0
    rows.append({
        "file_id": f"itw_{i:06d}", "path": str(p),
        "dataset": "in-the-wild", "label": infer_label(p),
        "speaker_id": "unknown", "generator_id": "unknown", "source_id": "unknown",
        "duration_seconds": dur, "sample_rate": sr, "channels": ch,
        "format": p.suffix.lower().lstrip("."), "sha256": sha,
        "duplicate_of": dup_of or "",
    })

df_man = pd.DataFrame(rows)
df_man.to_csv(METADATA / "itw_manifest.csv", index=False)
print(f"Manifest saved: {len(df_man)} files, duplicates: {(df_man.duplicate_of != '').sum()}")
label_dist = dict(df_man.label.value_counts())
print(f"Labels: {label_dist}")

# Guard: if all labels are unknown, stop rather than silently compute nonsense
known = df_man[df_man.label.isin(["FAKE", "REAL"])]
if len(known) == 0:
    print("\nERROR: Label inference produced 0 FAKE/REAL labels.")
    print("  The ITW CSV was not found or could not be parsed.")
    print("  Check the extracted directory structure printed in Step 1b above.")
    print("  You may need to update _load_itw_metadata_csv() with the actual CSV filename/columns.")
    sys.exit(1)
if len(known["label"].unique()) < 2:
    print(f"\nERROR: Only one class present after label inference: {label_dist}")
    print("  ROC-AUC requires both FAKE and REAL samples. Cannot proceed.")
    sys.exit(1)
print(f"  {len(known)} labelled files ({known.label.value_counts().to_dict()}) — proceeding.")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Extract features
# ─────────────────────────────────────────────────────────────────────────────
print("\n[Step 5] Extracting features...")
sys.path.insert(0, str(ROOT))
from features.extractor import extract_features

feat_rows, fails = [], 0
for i, (_, row) in enumerate(known.iterrows()):
    if i % 500 == 0:
        print(f"  features [{i}/{len(known)}]")
    feat, err = extract_features(row.path, cms=True)
    if feat is None:
        fails += 1
        continue
    rec = {"file_id": row.file_id, "label": row.label}
    for k in FEATURE_NAMES:
        rec[k] = feat.get(k, 0.0)
    feat_rows.append(rec)

df_itw_feat = pd.DataFrame(feat_rows)
df_itw_feat.to_csv(FEATURES / "itw_features.csv", index=False)
print(f"Features: {len(feat_rows)} ok, {fails} failed")

if len(feat_rows) == 0:
    print("ERROR: No features extracted. Cannot evaluate.")
    sys.exit(1)
if len(df_itw_feat["label"].unique()) < 2:
    print(f"ERROR: Only one class in feature set: {df_itw_feat['label'].value_counts().to_dict()}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Cross-dataset evaluation: FOR-2sec → ITW
# ─────────────────────────────────────────────────────────────────────────────
print("\n[Step 6] Cross-dataset evaluation (FOR-2sec models → ITW)...")
print("  NOTE: These models were trained on FOR-2sec which has a confirmed codec confound.")
print("  Results are EXPERIMENTAL ONLY and must not be used for production decisions.")

rf = joblib.load(MODELS / "random_forest.joblib")
lr = joblib.load(MODELS / "logistic_regression.joblib")
sc = joblib.load(MODELS / "scaler.joblib")

X_itw = df_itw_feat[FEATURE_NAMES].values.astype(np.float64)
y_itw = df_itw_feat["label"].map(LABEL_MAP).values

rf_p  = rf.predict_proba(X_itw)[:, 1]
lr_p  = lr.predict_proba(sc.transform(X_itw))[:, 1]

def mets(yt, yp, ypr, name):
    tn, fp, fn, tp = confusion_matrix(yt, yp, labels=[0, 1]).ravel()
    fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (tn + fp) if (tn + fp) > 0 else 0.0
    return {
        "split": name,
        "accuracy":  round(float(accuracy_score(yt, yp)), 4),
        "f1":        round(float(f1_score(yt, yp, zero_division=0)), 4),
        "precision": round(float(precision_score(yt, yp, zero_division=0)), 4),
        "recall":    round(float(recall_score(yt, yp, zero_division=0)), 4),
        "fnr":       round(float(fnr), 4),
        "fpr":       round(float(fpr), 4),
        "roc_auc":   round(float(roc_auc_score(yt, ypr)), 4),
        "n_samples": int(len(yt)),
        "class_dist": {"REAL": int((yt == 0).sum()), "FAKE": int((yt == 1).sum())},
        "cm": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }

rf_res = mets(y_itw, (rf_p >= 0.5).astype(int), rf_p, "FOR->ITW RF")
lr_res = mets(y_itw, (lr_p >= 0.5).astype(int), lr_p, "FOR->ITW LR")

print(f"  FOR->ITW RF: AUC={rf_res['roc_auc']:.4f}  FNR={rf_res['fnr']:.4f}  FPR={rf_res['fpr']:.4f}")
print(f"  FOR->ITW LR: AUC={lr_res['roc_auc']:.4f}  FNR={lr_res['fnr']:.4f}  FPR={lr_res['fpr']:.4f}")

results = {
    "experiment_note": (
        "FOR-2sec models have a confirmed codec confound (RF test AUC 0.47). "
        "These cross-dataset results are EXPERIMENTAL ONLY."
    ),
    "for_to_itw_rf": rf_res,
    "for_to_itw_lr": lr_res,
}
with open(MODELS / "cross_dataset_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved: models/cross_dataset_results.json")
print("\nDone. Review the AUC values above before proceeding to next phase.")
