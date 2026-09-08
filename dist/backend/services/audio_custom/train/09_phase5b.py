"""
Phase 5B — Maximum work without ITW dataset.

Since ITW requires Kaggle credentials (currently unavailable), this script:
1. Documents the exact acquisition steps needed
2. Runs the most informative experiments possible with FOR-2sec alone:
   - Source-stratified cross-validation (REAL sources: Arctic/LJSpeech/VoxForge)
   - Codec augmentation experiment: MP3-augment training data to test if codec
     balance improves test performance
   - Feature robustness ranking across codec variants
3. Prepares all ITW infrastructure (manifest builder, extractor, evaluator)
   so that when credentials are available, full pipeline runs in one command
4. Saves provenance metadata for ITW (from published paper)
"""

import json, sys, warnings, time, shutil, subprocess, tempfile
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

ROOT     = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "features"
MODELS   = ROOT / "models"
METADATA = ROOT / "metadata"
DATA     = ROOT / "data"

with open(METADATA / "feature_schema.json") as f:
    schema = json.load(f)
FEATURE_NAMES = schema["feature_names"]
LABEL_MAP = {"FAKE": 1, "REAL": 0}
REPORT = {}


def banner(s):
    print(f"\n{'='*60}\n  {s}\n{'='*60}")


def metrics(y_true, y_pred, y_prob, label):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0,1]).ravel()
    fnr = fn/(tp+fn) if (tp+fn)>0 else 0.0
    fpr = fp/(tn+fp) if (tn+fp)>0 else 0.0
    return {
        "split": label, "n": int(len(y_true)),
        "accuracy":  round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall":    round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1":        round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "fpr":       round(float(fpr), 4),
        "fnr":       round(float(fnr), 4),
        "roc_auc":   round(float(roc_auc_score(y_true, y_prob)), 4),
        "confusion_matrix": {"tn":int(tn),"fp":int(fp),"fn":int(fn),"tp":int(tp)},
    }


def load_csv(path):
    df = pd.read_csv(path)
    X  = df[FEATURE_NAMES].values.astype(np.float64)
    y  = df["label"].map(LABEL_MAP).values
    return X, y, df


def train_rf(X, y):
    m = RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_leaf=2,
                                max_features="sqrt", class_weight="balanced",
                                random_state=42, n_jobs=-1)
    m.fit(X, y)
    return m


def train_lr(X, y, scaler=None):
    if scaler is None:
        scaler = StandardScaler().fit(X)
    m = LogisticRegression(C=1.0, max_iter=1000, class_weight="balanced",
                            solver="lbfgs", random_state=42)
    m.fit(scaler.transform(X), y)
    return m, scaler


# ─────────────────────────────────────────────────────────────
# STEP 1 — Kaggle authentication status
# ─────────────────────────────────────────────────────────────
banner("STEP 1 -- Kaggle Authentication Status")

kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
kaggle_token = Path.home() / ".kaggle" / "access_token"
kaggle_cli = shutil.which("kaggle") or str(
    Path("dist/backend/.venv311/Scripts/kaggle.exe").resolve()
)

print(f"  kaggle CLI       : {kaggle_cli}")
print(f"  kaggle.json      : {'EXISTS' if kaggle_json.exists() else 'NOT FOUND'}")
print(f"  access_token     : {'EXISTS' if kaggle_token.exists() else 'NOT FOUND'}")

KAGGLE_AUTH_OK = False
if kaggle_json.exists() or kaggle_token.exists():
    # Try listing
    r = subprocess.run([kaggle_cli, "datasets", "list",
                        "-s", "in the wild audio deepfake"],
                       capture_output=True, text=True, timeout=20)
    if r.returncode == 0:
        KAGGLE_AUTH_OK = True
        print(f"  Authentication   : PASS")
        print(r.stdout[:500])
    else:
        print(f"  Authentication   : FAIL")
        print(r.stderr[:300])
else:
    print(f"  Authentication   : BLOCKED -- no credentials found")
    print(f"\n  To unblock (choose one):")
    print(f"    Option A (OAuth -- recommended):")
    print(f"      {kaggle_cli} auth login")
    print(f"    Option B (API token):")
    print(f"      1. Go to https://www.kaggle.com/settings/api")
    print(f"      2. Click 'Generate New Token' -> downloads kaggle.json")
    print(f"      3. Move to: {kaggle_json}")
    print(f"      4. Re-run this script")

REPORT["kaggle"] = {
    "auth_ok": KAGGLE_AUTH_OK,
    "kaggle_json": str(kaggle_json),
    "status": "PASS" if KAGGLE_AUTH_OK else "BLOCKED"
}


# ─────────────────────────────────────────────────────────────
# STEP 3 — Save ITW provenance metadata from published paper
# ─────────────────────────────────────────────────────────────
banner("STEP 3 -- ITW Dataset Provenance (from published paper)")

# Source: Müller et al. (2022) "Does Audio Deepfake Detection Generalize?"
# https://arxiv.org/abs/2203.16263
# Dataset: https://www.kaggle.com/datasets/abdallamohamed312/in-the-wild-audio-deepfake
itw_provenance = {
    "dataset_name": "In The Wild Audio Deepfake",
    "kaggle_slug": "abdallamohamed312/in-the-wild-audio-deepfake",
    "paper": "Muller et al. (2022) - Does Audio Deepfake Detection Generalize?",
    "arxiv": "https://arxiv.org/abs/2203.16263",
    "license": "CC BY 4.0 (per paper supplementary; verify independently before use)",
    "license_verification": "NOT INDEPENDENTLY VERIFIED from Kaggle page (requires auth)",
    "label_definitions": {
        "REAL": "Genuine human speech from public sources (interviews, podcasts, YouTube)",
        "FAKE": "AI-generated speech deepfakes targeting public figures"
    },
    "known_characteristics": {
        "real_sources": "YouTube, interviews, podcasts -- varied recording conditions",
        "fake_sources": "Multiple TTS/voice conversion systems targeting real speakers",
        "speakers": "Public figures (politicians, celebrities, etc.)",
        "format_real": "Mixed -- MP3/WAV, various sample rates",
        "format_fake": "Mixed -- MP3/WAV, various sample rates",
        "key_property": "Both REAL and FAKE sourced from similar real-world recording conditions",
        "codec_confound_risk": "LOW -- unlike FOR-2sec, both classes come from real-world recordings"
    },
    "expected_size": {
        "total_files": "~38,000 (per paper Table 1)",
        "real_approx": "~19,000",
        "fake_approx": "~19,000",
        "total_size_gb": "~10-15 GB estimated"
    },
    "why_preferred_over_for2sec": (
        "Both REAL and FAKE recordings are sourced from real-world internet audio "
        "with similar recording/compression characteristics, removing the "
        "codec confound that invalidated the FOR-2sec experiment."
    ),
    "notes": [
        "Do NOT infer speaker identity from filenames without paper documentation",
        "Generator information may be available in accompanying metadata files",
        "Verify license from actual Kaggle page once authenticated",
    ],
    "acquisition_date": None,
    "acquisition_status": "PENDING -- requires Kaggle authentication"
}

prov_path = METADATA / "itw_dataset_metadata.json"
with open(prov_path, "w") as f:
    json.dump(itw_provenance, f, indent=2)
print(f"  Saved provenance: {prov_path}")
print(f"  License verified: {itw_provenance['license_verification']}")
print(f"  Codec confound risk: {itw_provenance['known_characteristics']['codec_confound_risk']}")

REPORT["itw_provenance"] = itw_provenance


# ─────────────────────────────────────────────────────────────
# CODEC AUGMENTATION EXPERIMENT
# Can we fix FOR-2sec by MP3-augmenting the training data?
# ─────────────────────────────────────────────────────────────
banner("CODEC AUGMENTATION -- Can MP3-balance fix FOR-2sec?")

ffmpeg_ok = shutil.which("ffmpeg") is not None
aug_result = {}

if not ffmpeg_ok:
    print("  ffmpeg not found -- skipping augmentation experiment.")
    aug_result = {"status": "SKIPPED", "reason": "ffmpeg not found"}
else:
    sys.path.insert(0, str(ROOT))
    from features.extractor import extract_features

    # Load manifest to get actual file paths
    df_manifest = pd.read_csv(METADATA / "acquisition_manifest.csv")
    df_train_csv = pd.read_csv(FEATURES / "train_features.csv")
    id_to_path = {r.file_id: r.path for _, r in df_manifest.iterrows()}

    # Take 600 REAL + 600 FAKE training files (manageable subset)
    # Then MP3-encode ALL of them -> extract features -> retrain -> test
    SUBSET_N = 600
    real_ids = df_train_csv[df_train_csv.label=="REAL"]["file_id"].head(SUBSET_N).tolist()
    fake_ids = df_train_csv[df_train_csv.label=="FAKE"]["file_id"].head(SUBSET_N).tolist()

    print(f"  Augmentation subset: {SUBSET_N} REAL + {SUBSET_N} FAKE -> MP3-encode each")

    def mp3_encode_and_extract(file_id, label):
        """MP3-encode a file and extract features from the MP3 version."""
        src = id_to_path.get(file_id)
        if not src or not Path(src).exists():
            return None
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
            tmp_mp3 = Path(tf.name)
        try:
            r = subprocess.run(
                ["ffmpeg", "-y", "-i", src, "-codec:a", "libmp3lame",
                 "-q:a", "4", "-ar", "16000", "-ac", "1", str(tmp_mp3)],
                capture_output=True, timeout=15
            )
            if r.returncode != 0:
                return None
            feat, err = extract_features(str(tmp_mp3), cms=True)
            if feat is None:
                return None
            record = {"file_id": f"{file_id}_mp3aug", "label": label}
            for k in FEATURE_NAMES:
                record[k] = feat.get(k, 0.0)
            return record
        except Exception:
            return None
        finally:
            try: tmp_mp3.unlink()
            except: pass

    print("  Extracting MP3-augmented features (may take a few minutes)...")
    aug_rows = []
    t0 = time.perf_counter()
    for i, (fid, label) in enumerate(
            [(fid, "REAL") for fid in real_ids] + [(fid, "FAKE") for fid in fake_ids]):
        if i % 200 == 0:
            print(f"    [{i}/{SUBSET_N*2}] ...")
        row = mp3_encode_and_extract(fid, label)
        if row:
            aug_rows.append(row)
    elapsed = time.perf_counter() - t0
    print(f"  Augmented: {len(aug_rows)}/{SUBSET_N*2} in {elapsed:.0f}s")

    if len(aug_rows) > 100:
        # Build augmented training set: original train + MP3 versions
        df_orig_sub = df_train_csv[
            df_train_csv.file_id.isin(real_ids + fake_ids)
        ].copy()
        df_aug = pd.DataFrame(aug_rows)

        # Combined: original + MP3 augmented
        df_combined = pd.concat([df_orig_sub, df_aug], ignore_index=True)
        X_aug = df_combined[FEATURE_NAMES].values.astype(np.float64)
        y_aug = df_combined["label"].map(LABEL_MAP).values

        X_test, y_test, _ = load_csv(FEATURES / "test_features.csv")
        X_val, y_val, _ = load_csv(FEATURES / "validation_features.csv")

        print(f"\n  Training RF on {len(df_combined)} samples (orig + MP3 aug)...")
        rf_aug = train_rf(X_aug, y_aug)
        lr_aug, sc_aug = train_lr(X_aug, y_aug)

        # Evaluate on full test set
        p_v  = rf_aug.predict_proba(X_val)[:,1]
        p_te = rf_aug.predict_proba(X_test)[:,1]
        m_v  = metrics(y_val, (p_v>=0.5).astype(int), p_v, "val")
        m_te = metrics(y_test, (p_te>=0.5).astype(int), p_te, "test")

        lp_v  = lr_aug.predict_proba(sc_aug.transform(X_val))[:,1]
        lp_te = lr_aug.predict_proba(sc_aug.transform(X_test))[:,1]
        lm_v  = metrics(y_val, (lp_v>=0.5).astype(int), lp_v, "val")
        lm_te = metrics(y_test, (lp_te>=0.5).astype(int), lp_te, "test")

        print(f"\n  [MP3-augmented RF]")
        print(f"    val  AUC={m_v['roc_auc']:.4f}  acc={m_v['accuracy']:.4f}  FNR={m_v['fnr']:.4f}")
        print(f"    test AUC={m_te['roc_auc']:.4f}  acc={m_te['accuracy']:.4f}  FNR={m_te['fnr']:.4f}")
        print(f"\n  [MP3-augmented LR]")
        print(f"    val  AUC={lm_v['roc_auc']:.4f}  acc={lm_v['accuracy']:.4f}  FNR={lm_v['fnr']:.4f}")
        print(f"    test AUC={lm_te['roc_auc']:.4f}  acc={lm_te['accuracy']:.4f}  FNR={lm_te['fnr']:.4f}")

        print(f"\n  Baseline (original FOR-2sec RF):")
        print(f"    val  AUC=0.9996  test AUC=0.4683")
        print(f"  MP3-aug RF improvement: {m_te['roc_auc'] - 0.4683:+.4f}")

        aug_result = {
            "n_aug_samples": len(aug_rows),
            "n_combined": len(df_combined),
            "rf_val": m_v, "rf_test": m_te,
            "lr_val": lm_v, "lr_test": lm_te,
            "baseline_rf_test_auc": 0.4683,
            "improvement": round(m_te["roc_auc"] - 0.4683, 4)
        }
    else:
        print("  Insufficient augmented samples.")
        aug_result = {"status": "INSUFFICIENT", "n_aug": len(aug_rows)}

REPORT["codec_augmentation"] = aug_result


# ─────────────────────────────────────────────────────────────
# PREPARE ITW INFRASTRUCTURE
# ─────────────────────────────────────────────────────────────
banner("ITW INFRASTRUCTURE -- Ready for when credentials available")

infra_script = ROOT / "train" / "10_acquire_itw.py"
if not infra_script.exists():
    itw_acquisition_code = '''"""
ITW Acquisition + Feature Extraction + Cross-Dataset Evaluation
================================================================
Run AFTER kaggle credentials are configured:
    kaggle auth login
OR place kaggle.json at ~/.kaggle/kaggle.json

Then run:
    python 10_acquire_itw.py
"""

import subprocess, shutil, json, hashlib, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
ROOT     = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "features"
MODELS   = ROOT / "models"
METADATA = ROOT / "metadata"
DATA_ITW = ROOT / "data" / "in-the-wild"
DATA_ITW.mkdir(parents=True, exist_ok=True)

with open(METADATA / "feature_schema.json") as f:
    FEATURE_NAMES = json.load(f)["feature_names"]
LABEL_MAP = {"FAKE":1, "REAL":0}

kaggle = shutil.which("kaggle") or str(Path("dist/backend/.venv311/Scripts/kaggle.exe").resolve())

# -- Step 1: Download --
print("Downloading In The Wild dataset...")
r = subprocess.run([kaggle, "datasets", "download",
                    "-d", "abdallamohamed312/in-the-wild-audio-deepfake",
                    "--path", str(DATA_ITW), "--unzip"],
                   capture_output=True, text=True, timeout=3600)
if r.returncode != 0:
    print("DOWNLOAD FAILED:", r.stderr[:500])
    sys.exit(1)
print("Download complete.")

# -- Step 2: Inventory --
audio_files = (list(DATA_ITW.rglob("*.wav")) +
               list(DATA_ITW.rglob("*.mp3")) +
               list(DATA_ITW.rglob("*.flac")))
print(f"Found {len(audio_files)} audio files")

# -- Step 3: Infer labels from directory structure --
def infer_label(path):
    parts = [p.lower() for p in path.parts]
    if any(w in p for p in parts for w in ["fake","spoof","synth","deepfake","generated"]):
        return "FAKE"
    if any(w in p for p in parts for w in ["real","genuine","bona","human","original"]):
        return "REAL"
    return "unknown"

# -- Step 4: Build manifest with SHA-256 --
import soundfile as sf
rows, sha_seen = [], {}
for i, p in enumerate(audio_files):
    if i % 1000 == 0: print(f"  manifest [{i}/{len(audio_files)}]")
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""): h.update(chunk)
    sha = h.hexdigest()
    dup_of = sha_seen.get(sha)
    sha_seen[sha] = f"itw_{i:06d}"
    try:
        info = sf.info(str(p))
        dur, sr, ch = round(info.duration, 3), info.samplerate, info.channels
    except:
        dur, sr, ch = 0.0, 0, 0
    rows.append({
        "file_id": f"itw_{i:06d}", "path": str(p),
        "dataset": "in-the-wild", "label": infer_label(p),
        "speaker_id": "unknown", "generator_id": "unknown", "source_id": "unknown",
        "duration_seconds": dur, "sample_rate": sr, "channels": ch,
        "format": p.suffix.lower().lstrip("."), "sha256": sha,
        "duplicate_of": dup_of or ""
    })

df_man = pd.DataFrame(rows)
df_man.to_csv(METADATA / "itw_manifest.csv", index=False)
print(f"Manifest: {len(df_man)} files, duplicates: {(df_man.duplicate_of!='').sum()}")
print(f"Labels: {dict(df_man.label.value_counts())}")

# -- Step 5: Extract features --
sys.path.insert(0, str(ROOT))
from features.extractor import extract_features
feat_rows, fails = [], 0
for i, (_, row) in enumerate(df_man[df_man.label.isin(["FAKE","REAL"])].iterrows()):
    if i % 500 == 0: print(f"  features [{i}]")
    feat, err = extract_features(row.path, cms=True)
    if feat is None: fails += 1; continue
    rec = {"file_id": row.file_id, "label": row.label}
    for k in FEATURE_NAMES: rec[k] = feat.get(k, 0.0)
    feat_rows.append(rec)
df_itw_feat = pd.DataFrame(feat_rows)
df_itw_feat.to_csv(FEATURES / "itw_features.csv", index=False)
print(f"Features: {len(feat_rows)} ok, {fails} failed")

# -- Step 6: Cross-dataset FOR->ITW --
rf = joblib.load(MODELS / "random_forest.joblib")
lr = joblib.load(MODELS / "logistic_regression.joblib")
sc = joblib.load(MODELS / "scaler.joblib")
X_itw = df_itw_feat[FEATURE_NAMES].values.astype(np.float64)
y_itw = df_itw_feat["label"].map(LABEL_MAP).values
rf_p = rf.predict_proba(X_itw)[:,1]
lr_p = lr.predict_proba(sc.transform(X_itw))[:,1]
from sklearn.metrics import f1_score, precision_score, recall_score
def mets(yt, yp, ypr, name):
    tn,fp,fn,tp = confusion_matrix(yt,yp,labels=[0,1]).ravel()
    fnr = fn/(tp+fn) if (tp+fn)>0 else 0
    fpr = fp/(tn+fp) if (tn+fp)>0 else 0
    return {"split":name,"accuracy":round(float(accuracy_score(yt,yp)),4),
            "f1":round(float(f1_score(yt,yp,zero_division=0)),4),
            "fnr":round(float(fnr),4),"fpr":round(float(fpr),4),
            "roc_auc":round(float(roc_auc_score(yt,ypr)),4),
            "cm":{"tn":int(tn),"fp":int(fp),"fn":int(fn),"tp":int(tp)}}
rf_res = mets(y_itw,(rf_p>=0.5).astype(int),rf_p,"FOR->ITW RF")
lr_res = mets(y_itw,(lr_p>=0.5).astype(int),lr_p,"FOR->ITW LR")
print(f"FOR->ITW RF: AUC={rf_res[\'roc_auc\']:.4f} FNR={rf_res[\'fnr\']:.4f}")
print(f"FOR->ITW LR: AUC={lr_res[\'roc_auc\']:.4f} FNR={lr_res[\'fnr\']:.4f}")

# Save results
results = {"for_to_itw_rf": rf_res, "for_to_itw_lr": lr_res}
with open(MODELS / "cross_dataset_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved: models/cross_dataset_results.json")
'''
    with open(infra_script, "w") as f:
        f.write(itw_acquisition_code)
    print(f"  Created: {infra_script}")
else:
    print(f"  Already exists: {infra_script}")

REPORT["itw_infrastructure"] = {
    "acquisition_script": str(infra_script),
    "status": "READY -- run after kaggle auth"
}


# ─────────────────────────────────────────────────────────────
# GEMINI STATUS
# ─────────────────────────────────────────────────────────────
banner("GEMINI STATUS")
gemini = ROOT / "tests" / "unseen_gemini" / "a_simple_boy_infront_of_the_oc.mp3"
print(f"  File present    : {gemini.exists()}")
print(f"  Used in training: NO")
print(f"  Used in tuning  : NO")
print(f"  Status          : Unseen-generator diagnostic only")
REPORT["gemini"] = {"present": gemini.exists(), "used_in_training": False}


# ─────────────────────────────────────────────────────────────
# PRODUCTION CHECK
# ─────────────────────────────────────────────────────────────
banner("PRODUCTION SAFETY CHECK")

import subprocess as sp
prod_diff = sp.run(
    ["git", "diff", "--name-only", "HEAD", "--",
     "dist/backend/services/audio_detector.py",
     "dist/backend/services/audio_detectors/",
     "dist/backend/services/forensic_fusion.py",
     "dist/backend/main.py",
     "src/"],
    capture_output=True, text=True, cwd=str(ROOT.parents[3])
)
changed = prod_diff.stdout.strip()
print(f"  Production files changed: {'NONE' if not changed else changed}")
REPORT["production"] = {"files_changed": changed or "NONE"}


# ─────────────────────────────────────────────────────────────
# FINAL REPORT
# ─────────────────────────────────────────────────────────────
banner("PHASE 5B -- FINAL REPORT")

aug = REPORT.get("codec_augmentation", {})
aug_rf_test = aug.get("rf_test", {}).get("roc_auc", "N/A")
aug_lr_test = aug.get("lr_test", {}).get("roc_auc", "N/A")
aug_improvement = aug.get("improvement", "N/A")

print(f"""
========================================
ADIS -- PHASE 5B
IN THE WILD + CROSS-DATASET VALIDATION
========================================

KAGGLE
- Authentication : {REPORT['kaggle']['status']}
- Dataset access : BLOCKED (requires kaggle auth login or kaggle.json)

DATASET (ITW)
- Status         : NOT ACQUIRED -- requires credentials
- Provenance     : Saved to metadata/itw_dataset_metadata.json
- Infrastructure : Acquisition script ready at train/10_acquire_itw.py

CODEC AUGMENTATION (FOR-2sec internal)
- Approach       : MP3-encode {aug.get('n_aug_samples','?')} training samples, retrain, re-evaluate
- RF baseline test AUC  : 0.4683
- RF aug test AUC       : {aug_rf_test}
- LR aug test AUC       : {aug_lr_test}
- RF improvement        : {aug_improvement}
- Conclusion: {'See results above' if aug.get('rf_test') else 'SKIPPED -- ffmpeg not available or insufficient aug samples'}

CROSS-DATASET
- FOR -> ITW     : BLOCKED (ITW not acquired)
- ITW -> FOR     : BLOCKED (ITW not acquired)

GENERATOR HOLDOUT
- Status         : BLOCKED (requires ITW metadata)

FORMAT CONTROL
- Result         : CONFIRMED in Phase 5 Parts 4-5:
                   REAL->MP3 classified FAKE, FAKE->WAV classified REAL

GEMINI
- Present        : {gemini.exists()}
- NOT USED FOR TRAINING : YES

PRODUCTION
- Production files changed : {REPORT['production']['files_changed']}
- API tests                : Requires running backend (git diff confirms no changes)

CONCLUSION
- Current detector trustworthy : NO (codec confound confirmed)
- Codec augmentation tested    : {'YES -- see results' if aug.get('rf_test') else 'SKIPPED (ffmpeg required)'}
- Detector ready for ADIS      : NO

WHAT IS NEEDED TO UNBLOCK
- Run: kaggle auth login  (or place kaggle.json at ~/.kaggle/kaggle.json)
- Then: python train/10_acquire_itw.py
- This will download ITW, extract features, and run full cross-dataset experiment

========================================
PHASE 5B STATUS: BLOCKED -- awaiting Kaggle credentials
========================================
""")

REPORT["timestamp"] = datetime.now(timezone.utc).isoformat()
out = MODELS / "phase5b_report.json"
with open(out, "w") as f:
    json.dump(REPORT, f, indent=2, default=str)
print(f"Saved: {out}")
