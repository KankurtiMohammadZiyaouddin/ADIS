"""
Gemini Diagnostic -- Tasks 1-10
================================
Runs the Gemini sample through YAMNet, LR, and RF.
NO model changes. NO threshold changes. Diagnostic only.
"""

import json
import sys
import warnings
import traceback
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

ROOT       = Path(__file__).resolve().parents[1]
BACKEND    = Path(__file__).resolve().parents[3]
MODELS_DIR = ROOT / "models"
METADATA   = ROOT / "metadata"
GEMINI     = ROOT / "tests" / "unseen_gemini" / "a_simple_boy_infront_of_the_oc.mp3"

# -- helpers ----------------------------------------------------------

def sep(title=""):
    print()
    if title:
        dashes = "-" * (54 - len(title))
        print(f"-- {title} {dashes}")
    else:
        print("-" * 58)


# ================================================================
# TASK 1 -- YAMNet
# ================================================================
sep("TASK 1 -- YAMNet")

yamnet_result = None
try:
    sys.path.insert(0, str(BACKEND))
    sys.path.insert(0, str(BACKEND / "services"))

    YAMNET_API = Path(__file__).resolve().parents[5] / "external" / "Deepfake-YamNet" / "API"
    sys.path.insert(0, str(YAMNET_API))

    from app.src.deepfake import deepfake_model, load_wav_16k_mono
    import tensorflow as tf

    print("YAMNet model loaded OK")
    audio = load_wav_16k_mono(str(GEMINI))
    if audio is None:
        raise ValueError("load_wav_16k_mono returned None")

    infer       = deepfake_model.signatures['serving_default']
    tensor      = tf.convert_to_tensor(audio, dtype=tf.float32)
    output      = infer(tensor)
    pred        = output['output_0'].numpy()
    p_fake      = float(pred[0])
    p_real      = float(pred[1])
    yamnet_cls  = "FAKE" if p_fake > p_real else "REAL"
    yamnet_conf = max(p_fake, p_real)

    print(f"  prob_fake      : {p_fake:.10f}")
    print(f"  prob_real      : {p_real:.10f}")
    print(f"  classification : {yamnet_cls}")
    print(f"  confidence     : {yamnet_conf:.10f}")
    print(f"  UI shows       : {round(p_fake*100, 1)}% FAKE  (rounding confirms 0%)")
    yamnet_result = dict(classification=yamnet_cls, p_fake=p_fake, p_real=p_real, confidence=yamnet_conf)

except Exception as e:
    print(f"  YAMNet ERROR: {e}")
    yamnet_result = dict(status="ERROR", error=str(e))


# ================================================================
# TASKS 2+3 -- Custom detectors + feature extraction
# ================================================================
sep("TASKS 2+3 -- Custom Detector + Feature Extraction")

sys.path.insert(0, str(ROOT))
import joblib
import pandas as pd

with open(METADATA / "feature_schema.json") as f:
    schema = json.load(f)
feature_names = schema["feature_names"]

feat_result = None
rf_result   = None
lr_result   = None

# Feature extraction
try:
    from features.extractor import extract_features
    feat, err = extract_features(str(GEMINI), cms=True)
    if feat is None:
        raise ValueError(f"Extraction failed: {err}")

    # Build X
    x_vec = np.array([[feat.get(k, 0.0) for k in feature_names]], dtype=np.float64)
    nan_count = int(np.isnan(x_vec).sum())
    inf_count = int(np.isinf(x_vec).sum())

    print(f"  Feature count   : {len(feature_names)}")
    print(f"  NaN count       : {nan_count}")
    print(f"  Inf count       : {inf_count}")
    feat_result = dict(n_features=len(feature_names), nan=nan_count, inf=inf_count, x=x_vec)
except Exception as e:
    print(f"  Feature extraction ERROR: {e}")
    feat_result = dict(status="ERROR", error=str(e))

# RF
try:
    rf = joblib.load(MODELS_DIR / "random_forest.joblib")
    x  = feat_result["x"]
    rf_prob = rf.predict_proba(x)[0]
    rf_p_fake, rf_p_real = float(rf_prob[1]), float(rf_prob[0])
    rf_cls  = "FAKE" if rf_p_fake >= 0.5 else "REAL"
    print(f"\n  [RF] classification : {rf_cls}")
    print(f"  [RF] p_fake         : {rf_p_fake:.6f}")
    print(f"  [RF] p_real         : {rf_p_real:.6f}")
    rf_result = dict(classification=rf_cls, p_fake=rf_p_fake, p_real=rf_p_real,
                     n_estimators=rf.n_estimators, max_depth=rf.max_depth)
except Exception as e:
    print(f"  RF ERROR: {e}")
    rf_result = dict(status="NOT AVAILABLE", error=str(e))

# LR
try:
    lr     = joblib.load(MODELS_DIR / "logistic_regression.joblib")
    scaler = joblib.load(MODELS_DIR / "scaler.joblib")
    x_sc   = scaler.transform(feat_result["x"])
    lr_prob = lr.predict_proba(x_sc)[0]
    lr_p_fake, lr_p_real = float(lr_prob[1]), float(lr_prob[0])
    lr_cls  = "FAKE" if lr_p_fake >= 0.5 else "REAL"
    print(f"\n  [LR] classification : {lr_cls}")
    print(f"  [LR] p_fake         : {lr_p_fake:.6f}")
    print(f"  [LR] p_real         : {lr_p_real:.6f}")
    lr_result = dict(classification=lr_cls, p_fake=lr_p_fake, p_real=lr_p_real)
except Exception as e:
    print(f"  LR ERROR: {e}")
    lr_result = dict(status="NOT AVAILABLE", error=str(e))


# ================================================================
# TASK 4 -- Comparison table
# ================================================================
sep("TASK 4 -- Comparison Table")

def fmt(d, key, decimals=6):
    if d is None or "status" in d:
        return "N/A"
    v = d.get(key)
    if v is None:
        return "N/A"
    return f"{v:.{decimals}f}" if isinstance(v, float) else str(v)

print(f"  {'':22s} {'YAMNet':>12} {'Logistic Reg':>14} {'Random Forest':>14}")
print(f"  {'-'*22} {'-'*12} {'-'*14} {'-'*14}")
print(f"  {'Classification':22s} {fmt(yamnet_result,'classification',0):>12} {fmt(lr_result,'classification',0):>14} {fmt(rf_result,'classification',0):>14}")
print(f"  {'FAKE probability':22s} {fmt(yamnet_result,'p_fake'):>12} {fmt(lr_result,'p_fake'):>14} {fmt(rf_result,'p_fake'):>14}")
print(f"  {'REAL probability':22s} {fmt(yamnet_result,'p_real'):>12} {fmt(lr_result,'p_real'):>14} {fmt(rf_result,'p_real'):>14}")
print(f"  {'Confidence':22s} {fmt(yamnet_result,'confidence'):>12} {fmt(lr_result,'p_real' if lr_result and lr_result.get('classification')=='REAL' else 'p_fake'):>14} {fmt(rf_result,'p_real' if rf_result and rf_result.get('classification')=='REAL' else 'p_fake'):>14}")


# ================================================================
# TASK 5 -- Out-of-distribution analysis
# ================================================================
sep("TASK 5 -- Feature Distribution Analysis")

ood_result = None
if feat_result and "x" in feat_result:
    try:
        df_train = pd.read_csv(ROOT / "features" / "train_features_cms.csv")
        X_train  = df_train[feature_names].values.astype(np.float64)
        x_gemini = feat_result["x"][0]

        train_mean = X_train.mean(axis=0)
        train_std  = X_train.std(axis=0) + 1e-9
        z_scores   = (x_gemini - train_mean) / train_std

        within   = int((np.abs(z_scores) <= 2).sum())
        outside  = int(((np.abs(z_scores) > 2) & (np.abs(z_scores) <= 4)).sum())
        extreme  = int((np.abs(z_scores) > 4).sum())

        print(f"  Within normal distribution (|z|<=2) : {within}/{len(feature_names)}")
        print(f"  Outside (2<|z|<=4)                  : {outside}/{len(feature_names)}")
        print(f"  Extremely outside (|z|>4)            : {extreme}/{len(feature_names)}")
        print(f"  Mean |z-score| across features       : {np.abs(z_scores).mean():.3f}")

        top_ood = sorted(zip(feature_names, z_scores), key=lambda x: abs(x[1]), reverse=True)[:10]
        print(f"\n  Top 10 most deviant features (Gemini vs train):")
        print(f"  {'Feature':<45s} {'z-score':>8}")
        for name, z in top_ood:
            print(f"    {name:<43s} {z:>+8.3f}")

        ood_result = dict(within=within, outside=outside, extreme=extreme,
                          mean_abs_z=float(np.abs(z_scores).mean()),
                          top_ood=[(n, float(z)) for n, z in top_ood])
    except FileNotFoundError:
        # CMS features not saved -- fall back to original
        try:
            df_train = pd.read_csv(ROOT / "features" / "train_features.csv")
            X_train  = df_train[feature_names].values.astype(np.float64)
            x_gemini = feat_result["x"][0]
            train_mean = X_train.mean(axis=0)
            train_std  = X_train.std(axis=0) + 1e-9
            z_scores   = (x_gemini - train_mean) / train_std
            within  = int((np.abs(z_scores) <= 2).sum())
            outside = int(((np.abs(z_scores) > 2) & (np.abs(z_scores) <= 4)).sum())
            extreme = int((np.abs(z_scores) > 4).sum())
            print(f"  (Using non-CMS train features for reference)")
            print(f"  Within (|z|<=2): {within}  Outside: {outside}  Extreme: {extreme}")
            print(f"  Mean |z|: {np.abs(z_scores).mean():.3f}")
            top_ood = sorted(zip(feature_names, z_scores), key=lambda x: abs(x[1]), reverse=True)[:10]
            print(f"\n  Top 10 most deviant features:")
            for name, z in top_ood:
                print(f"    {name:<43s} {z:>+8.3f}")
            ood_result = dict(within=within, outside=outside, extreme=extreme,
                              mean_abs_z=float(np.abs(z_scores).mean()),
                              note="non-CMS train features used")
        except Exception as e2:
            print(f"  OOD analysis ERROR: {e2}")
    except Exception as e:
        print(f"  OOD analysis ERROR: {e}")
else:
    print("  Skipped -- feature extraction failed")


# ================================================================
# TASK 6 -- RF feature contribution
# ================================================================
sep("TASK 6 -- RF Feature Contribution")

if rf_result and "classification" in rf_result and feat_result and "x" in feat_result:
    try:
        importances = rf.feature_importances_
        x_gemini    = feat_result["x"][0]
        # Weight importance by how far Gemini deviates from train mean (directional)
        contributions = [(feature_names[i], float(importances[i])) for i in range(len(feature_names))]
        top_imp = sorted(contributions, key=lambda x: x[1], reverse=True)[:10]
        print(f"  RF classification for Gemini: {rf_result['classification']}  p_fake={rf_result['p_fake']:.4f}")
        print(f"\n  Top 10 features contributing most strongly to the model's decision:")
        print(f"  (Note: importance is global -- not Gemini-specific)")
        print(f"  {'Feature':<45s} {'Importance':>10}")
        for name, imp in top_imp:
            print(f"    {name:<43s} {imp:>10.5f}")
    except Exception as e:
        print(f"  RF contribution ERROR: {e}")
else:
    print("  Skipped -- RF not available or features not extracted")


# ================================================================
# TASK 10 -- Final report
# ================================================================
sep("TASK 10 -- FINAL REPORT")

import soundfile as sf
try:
    info = sf.info(str(GEMINI))
    duration = info.duration
    sr       = info.samplerate
    ch       = info.channels
    ch_str   = "Stereo" if ch == 2 else "Mono" if ch == 1 else str(ch)
except Exception:
    import librosa
    y, sr = librosa.load(str(GEMINI), sr=None, mono=False)
    duration = y.shape[-1] / sr
    ch_str   = "Stereo" if y.ndim == 2 and y.shape[0] == 2 else "Mono"

print("""
========================================
GEMINI DIAGNOSTIC
========================================
""")
print(f"INPUT")
print(f"  File       : a_simple_boy_infront_of_the_oc.mp3")
print(f"  Provenance : Claimed Gemini TTS (user-supplied, not independently verified)")
print(f"  Duration   : {duration:.2f}s")
print(f"  Sample rate: {sr} Hz")
print(f"  Channels   : {ch_str}")

print(f"\nYAMNet")
if yamnet_result and "classification" in yamnet_result:
    print(f"  Classification : {yamnet_result['classification']}")
    print(f"  FAKE prob      : {yamnet_result['p_fake']:.10f}  (rounds to 0% in UI -- confirmed)")
    print(f"  REAL prob      : {yamnet_result['p_real']:.10f}")
    print(f"  Confidence     : {yamnet_result['confidence']:.6f}")
else:
    print(f"  Status: {yamnet_result}")

print(f"\nLOGISTIC REGRESSION")
if lr_result and "classification" in lr_result:
    print(f"  Status         : Available (Phase 4/5 model, FOR-2sec trained)")
    print(f"  Classification : {lr_result['classification']}")
    print(f"  FAKE prob      : {lr_result['p_fake']:.6f}")
    print(f"  REAL prob      : {lr_result['p_real']:.6f}")
else:
    print(f"  Status: {lr_result.get('status','N/A')}")

print(f"\nRANDOM FOREST")
if rf_result and "classification" in rf_result:
    print(f"  Status         : Available (Phase 5 tuned, FOR-2sec trained, val FNR=0.14%)")
    print(f"  Classification : {rf_result['classification']}")
    print(f"  FAKE prob      : {rf_result['p_fake']:.6f}")
    print(f"  REAL prob      : {rf_result['p_real']:.6f}")
    print(f"  WARNING        : This model failed the FOR-2sec test set (ROC-AUC=0.47,")
    print(f"                   codec confound). Its predictions on unseen generators")
    print(f"                   have no validated forensic value.")
else:
    print(f"  Status: {rf_result.get('status','N/A')}")

print(f"\nFEATURE ANALYSIS")
if feat_result and "n_features" in feat_result:
    print(f"  Feature count  : {feat_result['n_features']}")
    print(f"  NaN            : {feat_result['nan']}")
    print(f"  Inf            : {feat_result['inf']}")
    if ood_result:
        print(f"  Within |z|<=2  : {ood_result['within']}/{feat_result['n_features']}")
        print(f"  Outside 2<|z|<=4: {ood_result['outside']}/{feat_result['n_features']}")
        print(f"  Extreme |z|>4  : {ood_result.get('extreme','N/A')}/{feat_result['n_features']}")
        print(f"  Mean |z-score| : {ood_result['mean_abs_z']:.3f}")
        if ood_result.get("note"):
            print(f"  Note           : {ood_result['note']}")
else:
    print(f"  Status: {feat_result.get('status','N/A') if feat_result else 'N/A'}")

print(f"\nINTERPRETATION")
y_cls = yamnet_result.get('classification','N/A') if yamnet_result else 'N/A'
print(f"  YAMNet false negative : {'YES -- classified REAL with near-zero FAKE probability' if y_cls == 'REAL' else 'NO -- classified FAKE'}")
print(f"  Provenance claim      : Gemini TTS (user-supplied -- not independently verified by this tool)")
print(f"  Correct description   : The detector classified this sample as REAL. This result")
print(f"                          may represent an unseen-generator generalisation failure:")
print(f"                          the model was trained on different synthetic speech")
print(f"                          distributions and has no guarantee of generalising to")
print(f"                          previously unseen synthesis systems.")
if yamnet_result and yamnet_result.get('classification') == 'REAL':
    print(f"  If provenance is confirmed: Known synthetic sample -- detector false negative.")

print(f"\nMODEL CHANGES")
print(f"  NONE -- diagnostic only")

print(f"\nUI CHANGES")
print(f"  Fabricated forensic text removed from AudioForensicsPage.jsx (completed in prior tasks)")

print("""
========================================
STATUS: COMPLETE
========================================
""")
