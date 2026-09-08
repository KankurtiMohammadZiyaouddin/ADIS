"""Diagnose the test CSV label inversion hypothesis."""
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.metrics import accuracy_score, roc_auc_score

ROOT = Path("dist/backend/services/audio_custom")
MODELS = ROOT / "models"
FEATURES = ROOT / "features"
METADATA = ROOT / "metadata"

with open(METADATA / "feature_schema.json") as f:
    schema = json.load(f)
feature_names = schema["feature_names"]

LABEL_MAP_NORMAL = {"FAKE": 1, "REAL": 0}
LABEL_MAP_INVERTED = {"FAKE": 0, "REAL": 1}

rf = joblib.load(MODELS / "random_forest.joblib")

# 1. Show label distribution per split
print("=== Label distributions ===")
for split in ["train", "validation", "test"]:
    df = pd.read_csv(FEATURES / f"{split}_features.csv")
    vc = dict(df["label"].value_counts())
    sample_labels = list(df["label"].head(5))
    print(f"  {split:12s}: {vc}  first5={sample_labels}")

# 2. Accuracy with normal vs inverted labels on test
print()
print("=== Test accuracy: normal vs inverted labels ===")
df_test = pd.read_csv(FEATURES / "test_features.csv")
X_test = df_test[feature_names].values.astype(np.float64)
prob = rf.predict_proba(X_test)[:, 1]
pred = (prob >= 0.5).astype(int)

y_normal = df_test["label"].map(LABEL_MAP_NORMAL).values
y_inverted = df_test["label"].map(LABEL_MAP_INVERTED).values

acc_normal = accuracy_score(y_normal, pred)
acc_inverted = accuracy_score(y_inverted, pred)
auc_normal = roc_auc_score(y_normal, prob)
auc_inverted = roc_auc_score(y_inverted, prob)

print(f"  Normal   labels: accuracy={acc_normal:.4f}  ROC-AUC={auc_normal:.4f}")
print(f"  Inverted labels: accuracy={acc_inverted:.4f}  ROC-AUC={auc_inverted:.4f}")

# 3. Check feature value ranges across splits
print()
print("=== Feature value sanity (first feature: band_energy_ratio_0_500hz) ===")
for split in ["train", "validation", "test"]:
    df = pd.read_csv(FEATURES / f"{split}_features.csv")
    col = feature_names[0]
    print(f"  {split:12s}: mean={df[col].mean():.4f}  std={df[col].std():.4f}  min={df[col].min():.4f}  max={df[col].max():.4f}")

# 4. Check if test file_ids match what we expect (FOR-2sec test/ directory)
print()
print("=== file_id prefixes in test split (first 5) ===")
df_test = pd.read_csv(FEATURES / "test_features.csv")
print(list(df_test["file_id"].head(5)))
print(f"  split column values: {list(df_test['split'].unique())}")

# 5. Check manifest to confirm test file assignments
print()
print("=== Cross-check manifest for test split ===")
df_manifest = pd.read_csv(ROOT / "metadata" / "dataset_manifest.csv")
test_manifest = df_manifest[df_manifest["split"] == "test"]
test_labels_manifest = dict(test_manifest["label"].value_counts())
test_file_ids = set(test_manifest["file_id"])
test_csv_ids = set(df_test["file_id"])
print(f"  Manifest test labels: {test_labels_manifest}")
print(f"  file_id overlap manifest vs CSV: {len(test_file_ids & test_csv_ids)}/{len(test_file_ids)}")

# Compare label per file_id between manifest and CSV
merged = df_test[["file_id", "label"]].merge(
    test_manifest[["file_id", "label"]].rename(columns={"label": "manifest_label"}),
    on="file_id", how="inner"
)
agree = (merged["label"] == merged["manifest_label"]).sum()
disagree = (merged["label"] != merged["manifest_label"]).sum()
print(f"  Label agreement manifest vs CSV: {agree} agree, {disagree} disagree out of {len(merged)}")
if disagree > 0:
    print("  LABEL MISMATCH DETECTED")
    print(merged[merged["label"] != merged["manifest_label"]].head(5).to_string())
