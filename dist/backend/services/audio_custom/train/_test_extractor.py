"""
Quick test of the feature extractor on a single file.
Run from repo root: dist\backend\.venv311\Scripts\python.exe dist\backend\services\audio_custom\train\_test_extractor.py
"""
import sys, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from features.extractor import extract_features, EXTRACTOR_CONFIG
from features.schema import build_feature_names

base = Path(__file__).resolve().parents[1] / "data" / "for-2sec" / "for-2seconds"
real_file = sorted((base / "training" / "real").glob("*.wav"))[0]
fake_file = sorted((base / "training" / "fake").glob("*.wav"))[0]

print(f"Testing REAL: {real_file.name}")
feat, err = extract_features(real_file)
if err:
    print(f"ERROR: {err}")
    sys.exit(1)

names = build_feature_names(feat)
print(f"Feature count (X): {len(names)}")
print(f"Total keys returned (incl. diagnostics): {len(feat)}")

# Determinism
feat2, _ = extract_features(real_file)
diffs = {k: (feat[k], feat2[k]) for k in feat if feat[k] != feat2[k]}
print(f"Determinism check: {'PASS' if not diffs else 'FAIL - ' + str(diffs)}")

# NaN/Inf
vec = [float(feat.get(k, 0.0)) for k in names]
bad = [names[i] for i, v in enumerate(vec) if not math.isfinite(v)]
print(f"NaN/Inf in REAL vector: {len(bad)}")
if bad:
    print(f"  BAD: {bad[:5]}")

# Feature groups
groups = {}
for n in names:
    if n.startswith("spectral_contrast"):      g = "spectral_contrast"
    elif n.startswith("spectral"):             g = "spectral"
    elif n.startswith("band_energy") or n in ("low_freq_energy_ratio", "high_freq_energy_ratio"): g = "band_energy"
    elif n.startswith("rms") or n.startswith("zcr") or n == "low_energy_ratio": g = "temporal"
    elif n.startswith("mfcc_delta2"):          g = "mfcc_delta2"
    elif n.startswith("mfcc_delta"):           g = "mfcc_delta"
    elif n.startswith("mfcc"):                 g = "mfcc"
    elif n.startswith("f0") or n == "voiced_ratio": g = "pitch"
    else:                                      g = "other"
    groups[g] = groups.get(g, 0) + 1

print()
print("Feature groups:")
for g, cnt in sorted(groups.items()):
    print(f"  {g:20s}: {cnt}")
print(f"  {'TOTAL':20s}: {sum(groups.values())}")

# Fake file test
print()
print(f"Testing FAKE: {fake_file.name}")
feat_f, err_f = extract_features(fake_file)
if err_f:
    print(f"  ERROR: {err_f}")
else:
    names_f = build_feature_names(feat_f)
    vec_f = [float(feat_f.get(k, 0.0)) for k in names_f]
    bad_f = [names_f[i] for i, v in enumerate(vec_f) if not math.isfinite(v)]
    print(f"  Feature count: {len(names_f)}, NaN/Inf: {len(bad_f)}, same schema: {names == names_f}")

print()
print("EXTRACTOR_CONFIG:")
for k, v in EXTRACTOR_CONFIG.items():
    print(f"  {k}: {v}")
