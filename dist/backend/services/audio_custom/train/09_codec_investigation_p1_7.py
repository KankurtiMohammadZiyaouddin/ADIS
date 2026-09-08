"""
Phase 5 Codec-Confound Investigation
======================================
Parts 1-7: Reproduce results, feature analysis, format experiment,
           ablation, shuffle sanity check.
NO model changes. NO production file changes.
"""

import json, sys, time, warnings, hashlib, subprocess, shutil, tempfile
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import joblib
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

ROOT       = Path(__file__).resolve().parents[1]
FEATURES   = ROOT / "features"
MODELS     = ROOT / "models"
METADATA   = ROOT / "metadata"
GEMINI     = ROOT / "tests" / "unseen_gemini" / "a_simple_boy_infront_of_the_oc.mp3"

with open(METADATA / "feature_schema.json") as f:
    schema = json.load(f)
FEATURE_NAMES = schema["feature_names"]
LABEL_MAP = {"FAKE": 1, "REAL": 0}
REPORT = {}


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


def banner(s):
    print(f"\n{'='*60}")
    print(f"  {s}")
    print(f"{'='*60}")


# ─────────────────────────────────────────────────────────────
# PART 1 — Reproduce existing evaluation
# ─────────────────────────────────────────────────────────────
banner("PART 1 -- Reproduce Existing Evaluation")

rf     = joblib.load(MODELS / "random_forest.joblib")
lr     = joblib.load(MODELS / "logistic_regression.joblib")
scaler = joblib.load(MODELS / "scaler.joblib")

X_train, y_train, _ = load_csv(FEATURES / "train_features.csv")
X_val,   y_val,   _ = load_csv(FEATURES / "validation_features.csv")
X_test,  y_test,  _ = load_csv(FEATURES / "test_features.csv")

X_val_sc  = scaler.transform(X_val)
X_test_sc = scaler.transform(X_test)

# RF
rf_prob_val  = rf.predict_proba(X_val)[:,1]
rf_prob_test = rf.predict_proba(X_test)[:,1]
rf_m_val  = metrics(y_val,  (rf_prob_val>=0.5).astype(int),  rf_prob_val,  "val")
rf_m_test = metrics(y_test, (rf_prob_test>=0.5).astype(int), rf_prob_test, "test")

# LR
lr_prob_val  = lr.predict_proba(X_val_sc)[:,1]
lr_prob_test = lr.predict_proba(X_test_sc)[:,1]
lr_m_val  = metrics(y_val,  (lr_prob_val>=0.5).astype(int),  lr_prob_val,  "val")
lr_m_test = metrics(y_test, (lr_prob_test>=0.5).astype(int), lr_prob_test, "test")

print(f"\n  RF  val  : acc={rf_m_val['accuracy']:.4f}  FNR={rf_m_val['fnr']:.4f}  AUC={rf_m_val['roc_auc']:.4f}")
print(f"  RF  test : acc={rf_m_test['accuracy']:.4f}  FNR={rf_m_test['fnr']:.4f}  AUC={rf_m_test['roc_auc']:.4f}")
print(f"  LR  val  : acc={lr_m_val['accuracy']:.4f}  FNR={lr_m_val['fnr']:.4f}  AUC={lr_m_val['roc_auc']:.4f}")
print(f"  LR  test : acc={lr_m_test['accuracy']:.4f}  FNR={lr_m_test['fnr']:.4f}  AUC={lr_m_test['roc_auc']:.4f}")
print(f"\n  RF test ROC-AUC = {rf_m_test['roc_auc']:.4f}  (expected ~0.47 -- confirmed: {'YES' if rf_m_test['roc_auc'] < 0.55 else 'DIFFERENT'})")

REPORT["part1"] = {
    "rf_val": rf_m_val, "rf_test": rf_m_test,
    "lr_val": lr_m_val, "lr_test": lr_m_test,
}


# ─────────────────────────────────────────────────────────────
# PART 2 — Feature-label association
# ─────────────────────────────────────────────────────────────
banner("PART 2 -- Feature-Label Association")

df_train_full = pd.read_csv(FEATURES / "train_features.csv")
X_tr_all = df_train_full[FEATURE_NAMES].values.astype(np.float64)
y_tr_all = df_train_full["label"].map(LABEL_MAP).values

rows = []
for i, fname in enumerate(FEATURE_NAMES):
    fake_vals = X_tr_all[y_tr_all==1, i]
    real_vals = X_tr_all[y_tr_all==0, i]
    pooled_std = np.sqrt((fake_vals.var() + real_vals.var()) / 2 + 1e-12)
    cohen_d    = (fake_vals.mean() - real_vals.mean()) / pooled_std
    stat, pval = stats.mannwhitneyu(fake_vals, real_vals, alternative='two-sided')
    n1, n2 = len(fake_vals), len(real_vals)
    r_rb   = 1 - (2*stat)/(n1*n2)          # rank-biserial correlation
    direction = "FAKE>REAL" if fake_vals.mean() > real_vals.mean() else "REAL>FAKE"
    rows.append({
        "feature":   fname,
        "cohen_d":   round(float(cohen_d), 5),
        "abs_cohen_d": round(float(abs(cohen_d)), 5),
        "rank_biserial": round(float(r_rb), 5),
        "mannwhitney_u": float(stat),
        "p_value":   float(pval),
        "direction": direction,
        "fake_mean": round(float(fake_vals.mean()), 5),
        "real_mean": round(float(real_vals.mean()), 5),
    })

df_assoc = pd.DataFrame(rows).sort_values("abs_cohen_d", ascending=False)
df_assoc.to_csv(METADATA / "feature_label_association.csv", index=False)
print(f"\n  Saved: metadata/feature_label_association.csv")
print(f"\n  Top 15 features by |Cohen's d|:")
print(f"  {'Feature':<45s} {'Cohen_d':>8}  {'Direction':<12}")
for _, row in df_assoc.head(15).iterrows():
    print(f"    {row.feature:<43s} {row.cohen_d:>+8.3f}  {row.direction}")

REPORT["part2"] = {"top15": df_assoc.head(15)[["feature","cohen_d","direction"]].to_dict("records")}


# ─────────────────────────────────────────────────────────────
# PART 3 — Identify potential codec/recording shortcuts
# ─────────────────────────────────────────────────────────────
banner("PART 3 -- Potential Codec/Recording Shortcut Features")

# Features that could plausibly be driven by recording/codec differences
# rather than synthesis characteristics
codec_sensitive_candidates = {
    "spectral_flatness_mean", "spectral_flatness_median", "spectral_flatness_std",
    "spectral_rolloff_mean", "spectral_rolloff_median", "spectral_rolloff_std",
    "high_freq_energy_ratio", "band_energy_ratio_4000_8000hz",
    "rms_mean", "rms_median", "rms_std", "rms_range",
    "spectral_bandwidth_mean", "spectral_bandwidth_median", "spectral_bandwidth_std",
    "band_energy_ratio_0_500hz", "low_freq_energy_ratio",
    "mfcc_1_mean",  # C1 encodes overall energy/loudness
    "zcr_mean", "zcr_median", "zcr_std",
}

print(f"\n  Checking {len(codec_sensitive_candidates)} candidate codec/recording-sensitive features:")
print(f"\n  {'Feature':<45s} {'Cohen_d':>8}  {'Rank'}")
flagged = []
for _, row in df_assoc.iterrows():
    if row.feature in codec_sensitive_candidates:
        rank = df_assoc.index.get_loc(_) + 1
        flagged.append({"feature": row.feature, "cohen_d": row.cohen_d, "rank": rank})
        print(f"    {row.feature:<43s} {row.cohen_d:>+8.3f}  #{rank}")

# Non-flagged top features (potentially more synthesis-driven)
synthesis_candidates = df_assoc[~df_assoc.feature.isin(codec_sensitive_candidates)].head(20)
print(f"\n  Top features NOT in codec-sensitive list (potentially synthesis-driven):")
for _, row in synthesis_candidates.head(10).iterrows():
    print(f"    {row.feature:<43s} {row.cohen_d:>+8.3f}  {row.direction}")

REPORT["part3"] = {
    "codec_sensitive_flagged": flagged,
    "top_synthesis_candidates": synthesis_candidates.head(10)[["feature","cohen_d","direction"]].to_dict("records"),
}


# ─────────────────────────────────────────────────────────────
# PART 4 — Format control experiment
# ─────────────────────────────────────────────────────────────
banner("PART 4 -- Format/Codec Control Experiment")

# Pick 5 REAL and 5 FAKE files from test split to transcode
df_test_df = pd.read_csv(FEATURES / "test_features.csv")
df_manifest = pd.read_csv(METADATA / "acquisition_manifest.csv")

test_real_ids = df_test_df[df_test_df.label=="REAL"]["file_id"].head(5).tolist()
test_fake_ids = df_test_df[df_test_df.label=="FAKE"]["file_id"].head(5).tolist()

id_to_path = {row.file_id: row.path for _, row in df_manifest.iterrows()}

sys.path.insert(0, str(ROOT))
from features.extractor import extract_features

def predict_from_file(path, cms=True):
    feat, err = extract_features(str(path), cms=cms)
    if feat is None:
        return None, err
    x = np.array([[feat.get(k, 0.0) for k in FEATURE_NAMES]], dtype=np.float64)
    rf_p = rf.predict_proba(x)[0, 1]
    lr_p = lr.predict_proba(scaler.transform(x))[0, 1]
    return {"rf_p_fake": round(float(rf_p), 4),
            "lr_p_fake": round(float(lr_p), 4),
            "rf_cls": "FAKE" if rf_p >= 0.5 else "REAL",
            "lr_cls": "FAKE" if lr_p >= 0.5 else "REAL"}, None

# Check if ffmpeg is available for transcoding
ffmpeg_ok = shutil.which("ffmpeg") is not None
print(f"\n  ffmpeg available: {ffmpeg_ok}")

format_results = []

if ffmpeg_ok:
    import soundfile as sf
    import librosa

    def transcode(src, dst, sr=None, mono=False, mp3=False):
        cmd = ["ffmpeg", "-y", "-i", str(src)]
        if sr:
            cmd += ["-ar", str(sr)]
        if mono:
            cmd += ["-ac", "1"]
        if mp3:
            cmd += ["-codec:a", "libmp3lame", "-q:a", "2"]
        else:
            cmd += ["-codec:a", "pcm_s16le"]
        cmd.append(str(dst))
        r = subprocess.run(cmd, capture_output=True, timeout=30)
        return r.returncode == 0

    sample_ids = test_real_ids[:3] + test_fake_ids[:3]
    sample_labels = ["REAL"]*3 + ["FAKE"]*3

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for fid, true_label in zip(sample_ids, sample_labels):
            src = id_to_path.get(fid)
            if not src or not Path(src).exists():
                continue

            variants = {
                "original_wav": src,
            }
            # WAV 16k mono
            dst_16k = tmp / f"{fid}_16k_mono.wav"
            if transcode(src, dst_16k, sr=16000, mono=True):
                variants["wav_16k_mono"] = str(dst_16k)
            # WAV 48k stereo (upsample)
            dst_48k = tmp / f"{fid}_48k_stereo.wav"
            if transcode(src, dst_48k, sr=48000):
                variants["wav_48k"] = str(dst_48k)
            # MP3 16k mono
            dst_mp3 = tmp / f"{fid}_16k_mono.mp3"
            if transcode(src, dst_mp3, sr=16000, mono=True, mp3=True):
                variants["mp3_16k_mono"] = str(dst_mp3)

            row = {"file_id": fid, "true_label": true_label}
            for variant_name, path in variants.items():
                result, err = predict_from_file(path)
                if result:
                    row[f"{variant_name}_rf"] = result["rf_cls"]
                    row[f"{variant_name}_rf_p"] = result["rf_p_fake"]
                    row[f"{variant_name}_lr"] = result["lr_cls"]
                    row[f"{variant_name}_lr_p"] = result["lr_p_fake"]
                else:
                    row[f"{variant_name}_rf"] = f"ERR:{err}"
            format_results.append(row)

    print(f"\n  Format control results ({len(format_results)} samples):")
    for r in format_results:
        print(f"\n  [{r['true_label']}] {r['file_id']}")
        for k, v in r.items():
            if k not in ("file_id", "true_label") and "_p" not in k:
                p_key = k.replace("_rf","_rf_p").replace("_lr","_lr_p")
                p_val = r.get(p_key, "?")
                print(f"      {k:<30s} RF={v}  p_fake={p_val}")
else:
    print("  ffmpeg not found -- skipping transcoding experiment.")
    print("  To run Part 4: install ffmpeg and rerun.")
    format_results = [{"status": "SKIPPED", "reason": "ffmpeg not found"}]

REPORT["part4"] = {"ffmpeg_available": ffmpeg_ok, "results": format_results}


# ─────────────────────────────────────────────────────────────
# PART 5 — Real/Fake cross-codec control
# ─────────────────────────────────────────────────────────────
banner("PART 5 -- Real/Fake Cross-Codec Control")

if ffmpeg_ok and format_results and "file_id" in format_results[0]:
    # Summarise from Part 4 results
    real_rows = [r for r in format_results if r.get("true_label") == "REAL"]
    fake_rows = [r for r in format_results if r.get("true_label") == "FAKE"]

    def avg_p(rows, key):
        vals = [r[key] for r in rows if key in r and isinstance(r[key], float)]
        return round(np.mean(vals), 4) if vals else None

    print(f"\n  Average RF p_fake by (true_label x format):")
    for label, rows in [("REAL", real_rows), ("FAKE", fake_rows)]:
        for variant in ["original_wav_rf_p", "wav_16k_mono_rf_p", "mp3_16k_mono_rf_p"]:
            ap = avg_p(rows, variant)
            print(f"    {label} {variant:<30s} avg p_fake={ap}")
    REPORT["part5"] = {"real_rows": real_rows, "fake_rows": fake_rows}
else:
    print("  Skipped (ffmpeg unavailable or Part 4 failed).")
    REPORT["part5"] = {"status": "SKIPPED"}


# ─────────────────────────────────────────────────────────────
# PART 6 — Feature ablation (Exp A / B / C)
# ─────────────────────────────────────────────────────────────
banner("PART 6 -- Feature Ablation")

# Experiment A: all 124 features (already done in Part 1 — reuse)
# Experiment B: remove codec-sensitive candidates
codec_feats = {f["feature"] for f in flagged}
features_B = [f for f in FEATURE_NAMES if f not in codec_feats]

# Experiment C: MFCC-std + delta-std + pitch + voicing + temporal only
# (relatively robust to codec; encoding doesn't strongly affect std of dynamics)
features_C = [f for f in FEATURE_NAMES if any([
    f.endswith("_std") and ("mfcc" in f),          # MFCC stdev
    f.startswith("mfcc_delta") and f.endswith("_std"),  # delta stdev
    f in {"f0_mean","f0_std","f0_median","f0_range","voiced_ratio"},  # pitch
    f in {"low_energy_ratio"},                      # temporal
    f.startswith("spectral_contrast"),              # contrast (more source-dependent)
])]

print(f"\n  Exp A: {len(FEATURE_NAMES)} features (all)")
print(f"  Exp B: {len(features_B)} features (codec-sensitive removed)")
print(f"  Exp C: {len(features_C)} features (MFCC-std + delta-std + pitch + contrast)")

def run_ablation(feat_list, label, X_tr, y_tr, X_v, y_v, X_te, y_te, X_v_for_scaler=None):
    idx = [FEATURE_NAMES.index(f) for f in feat_list]
    Xtr = X_tr[:, idx]
    Xv  = X_v[:, idx]
    Xte = X_te[:, idx]

    # RF
    rf_ab = RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_leaf=2,
                                    max_features="sqrt", class_weight="balanced",
                                    random_state=42, n_jobs=-1)
    rf_ab.fit(Xtr, y_tr)
    p_v  = rf_ab.predict_proba(Xv)[:,1]
    p_te = rf_ab.predict_proba(Xte)[:,1]
    m_v  = metrics(y_v,  (p_v>=0.5).astype(int),  p_v,  "val")
    m_te = metrics(y_te, (p_te>=0.5).astype(int), p_te, "test")

    # LR
    sc_ab = StandardScaler().fit(Xtr)
    lr_ab = LogisticRegression(C=1.0, max_iter=1000, class_weight="balanced",
                                solver="lbfgs", random_state=42)
    lr_ab.fit(sc_ab.transform(Xtr), y_tr)
    lp_v  = lr_ab.predict_proba(sc_ab.transform(Xv))[:,1]
    lp_te = lr_ab.predict_proba(sc_ab.transform(Xte))[:,1]
    lm_v  = metrics(y_v,  (lp_v>=0.5).astype(int),  lp_v,  "val")
    lm_te = metrics(y_te, (lp_te>=0.5).astype(int), lp_te, "test")

    print(f"\n  [{label}]  n_features={len(feat_list)}")
    print(f"    RF  val  AUC={m_v['roc_auc']:.4f}  acc={m_v['accuracy']:.4f}  FNR={m_v['fnr']:.4f}")
    print(f"    RF  test AUC={m_te['roc_auc']:.4f}  acc={m_te['accuracy']:.4f}  FNR={m_te['fnr']:.4f}")
    print(f"    LR  val  AUC={lm_v['roc_auc']:.4f}  acc={lm_v['accuracy']:.4f}  FNR={lm_v['fnr']:.4f}")
    print(f"    LR  test AUC={lm_te['roc_auc']:.4f}  acc={lm_te['accuracy']:.4f}  FNR={lm_te['fnr']:.4f}")
    return {"label": label, "n_features": len(feat_list),
            "rf_val": m_v, "rf_test": m_te,
            "lr_val": lm_v, "lr_test": lm_te}

ab_A = run_ablation(FEATURE_NAMES, "Exp-A all-124",  X_train, y_train, X_val, y_val, X_test, y_test)
ab_B = run_ablation(features_B,    "Exp-B no-codec", X_train, y_train, X_val, y_val, X_test, y_test)
ab_C = run_ablation(features_C,    "Exp-C robust",   X_train, y_train, X_val, y_val, X_test, y_test)

REPORT["part6"] = {"exp_A": ab_A, "exp_B": ab_B, "exp_C": ab_C,
                    "features_B": features_B, "features_C": features_C}


# ─────────────────────────────────────────────────────────────
# PART 7 — Shuffled-label sanity check
# ─────────────────────────────────────────────────────────────
banner("PART 7 -- Shuffled-Label Sanity Check")

rng = np.random.default_rng(42)
y_train_shuffled = rng.permutation(y_train)

rf_sh = RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_leaf=2,
                                max_features="sqrt", class_weight="balanced",
                                random_state=42, n_jobs=-1)
rf_sh.fit(X_train, y_train_shuffled)
p_sh = rf_sh.predict_proba(X_val)[:,1]
auc_sh = roc_auc_score(y_val, p_sh)
print(f"\n  Shuffled-label RF val ROC-AUC = {auc_sh:.4f}  (expected ~0.50)")
print(f"  {'PASS -- near chance' if abs(auc_sh - 0.5) < 0.05 else 'WARN -- unexpectedly far from 0.5'}")
REPORT["part7"] = {"shuffled_auc": round(float(auc_sh), 4),
                    "expected": "~0.50",
                    "pass": bool(abs(auc_sh - 0.5) < 0.05)}


# ─────────────────────────────────────────────────────────────
# Save investigation report
# ─────────────────────────────────────────────────────────────
REPORT["timestamp"] = datetime.now(timezone.utc).isoformat()
REPORT["phase"] = "Phase 5 -- Codec Confound Investigation Parts 1-7"

out = MODELS / "codec_investigation_p1_7.json"
with open(out, "w") as f:
    json.dump(REPORT, f, indent=2, default=str)
print(f"\n\nSaved: {out}")
print("\nParts 1-7 complete.")
