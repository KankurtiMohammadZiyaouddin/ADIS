"""Deep-dive diagnosis of test feature distribution vs train/val."""
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.metrics import roc_auc_score

ROOT = Path("dist/backend/services/audio_custom")
MODELS = ROOT / "models"
FEATURES = ROOT / "features"
METADATA = ROOT / "metadata"

with open(METADATA / "feature_schema.json") as f:
    schema = json.load(f)
feature_names = schema["feature_names"]
LABEL_MAP = {"FAKE": 1, "REAL": 0}

rf = joblib.load(MODELS / "random_forest.joblib")

df_train = pd.read_csv(FEATURES / "train_features.csv")
df_val   = pd.read_csv(FEATURES / "validation_features.csv")
df_test  = pd.read_csv(FEATURES / "test_features.csv")

X_train = df_train[feature_names].values.astype(np.float64)
X_val   = df_val[feature_names].values.astype(np.float64)
X_test  = df_test[feature_names].values.astype(np.float64)

y_train = df_train["label"].map(LABEL_MAP).values
y_val   = df_val["label"].map(LABEL_MAP).values
y_test  = df_test["label"].map(LABEL_MAP).values

# 1. p(FAKE) distribution per split
print("=== p(FAKE) distribution from RF ===")
for name, X, y in [("train", X_train, y_train), ("val", X_val, y_val), ("test", X_test, y_test)]:
    prob = rf.predict_proba(X)[:, 1]
    print(f"  {name:6s}: mean={prob.mean():.4f}  std={prob.std():.4f}  "
          f"median={np.median(prob):.4f}  min={prob.min():.4f}  max={prob.max():.4f}")
    # Breakdown by true label
    prob_fake = prob[y == 1]
    prob_real = prob[y == 0]
    print(f"          FAKE samples: p_fake mean={prob_fake.mean():.4f}  std={prob_fake.std():.4f}")
    print(f"          REAL samples: p_fake mean={prob_real.mean():.4f}  std={prob_real.std():.4f}")

# 2. Feature distribution shift — per-feature z-score of test mean relative to train
print()
print("=== Feature distribution shift (test vs train) ===")
train_mean = X_train.mean(axis=0)
train_std  = X_train.std(axis=0) + 1e-9
test_mean  = X_test.mean(axis=0)
z_scores   = (test_mean - train_mean) / train_std

top_shifted_idx = np.argsort(np.abs(z_scores))[::-1][:10]
print("  Top 10 most shifted features (|z-score| of test mean vs train mean):")
for i in top_shifted_idx:
    print(f"    {feature_names[i]:<45s} z={z_scores[i]:+.2f}  "
          f"train_mean={train_mean[i]:.4f}  test_mean={test_mean[i]:.4f}")

# 3. Range check: are test feature values within train range?
out_of_range = []
for i, name in enumerate(feature_names):
    t_min, t_max = X_train[:, i].min(), X_train[:, i].max()
    test_min, test_max = X_test[:, i].min(), X_test[:, i].max()
    n_below = (X_test[:, i] < t_min).sum()
    n_above = (X_test[:, i] > t_max).sum()
    if n_below + n_above > 0:
        out_of_range.append((name, n_below, n_above, t_min, t_max, test_min, test_max))

print(f"\n  Features with test values outside train range: {len(out_of_range)}")
for name, nb, na, tmin, tmax, tsmin, tsmax in out_of_range[:10]:
    print(f"    {name:<45s} below={nb} above={na}  train=[{tmin:.3f},{tmax:.3f}]  test=[{tsmin:.3f},{tsmax:.3f}]")

# 4. Check file_id format
print()
print("=== file_id samples ===")
print("  train:", list(df_train["file_id"].head(3)), "...", list(df_train["file_id"].tail(3)))
print("  val  :", list(df_val["file_id"].head(3)), "...", list(df_val["file_id"].tail(3)))
print("  test :", list(df_test["file_id"].head(3)), "...", list(df_test["file_id"].tail(3)))

# 5. Check the actual audio files to confirm they exist and match
print()
print("=== Spot-check audio file existence ===")
for split_name, df in [("train", df_train), ("val", df_val), ("test", df_test)]:
    # Check the split column value
    splits_in_col = df["split"].unique()
    print(f"  {split_name}: split col values = {list(splits_in_col)}")

# 6. Check manifest split column name
print()
print("=== Manifest columns ===")
df_acq = pd.read_csv(METADATA / "acquisition_manifest.csv")
print("  acquisition_manifest columns:", list(df_acq.columns))
df_ds = pd.read_csv(METADATA / "dataset_manifest.csv")
print("  dataset_manifest columns:", list(df_ds.columns))

# 7. Check split_A_standard.json
print()
print("=== split_A_standard.json structure ===")
with open(METADATA / "split_A_standard.json") as f:
    split_json = json.load(f)
print("  Keys:", list(split_json.keys()))
for key in split_json:
    v = split_json[key]
    if isinstance(v, dict):
        print(f"  {key}: keys={list(v.keys())}")
    elif isinstance(v, list):
        print(f"  {key}: n={len(v)}  first3={v[:3]}")
