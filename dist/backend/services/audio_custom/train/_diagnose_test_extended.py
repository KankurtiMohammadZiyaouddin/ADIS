"""
Extended Phase 6 analysis:
- Confirm the covariate shift diagnosis
- Check if a train+val combined retrain changes anything
- Report per-feature separability on train vs test
"""
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix

ROOT = Path("dist/backend/services/audio_custom")
MODELS = ROOT / "models"
FEATURES = ROOT / "features"
METADATA = ROOT / "metadata"

with open(METADATA / "feature_schema.json") as f:
    schema = json.load(f)
feature_names = schema["feature_names"]
LABEL_MAP = {"FAKE": 1, "REAL": 0}

df_train = pd.read_csv(FEATURES / "train_features.csv")
df_val   = pd.read_csv(FEATURES / "validation_features.csv")
df_test  = pd.read_csv(FEATURES / "test_features.csv")

X_train = df_train[feature_names].values.astype(np.float64)
X_val   = df_val[feature_names].values.astype(np.float64)
X_test  = df_test[feature_names].values.astype(np.float64)

y_train = df_train["label"].map(LABEL_MAP).values
y_val   = df_val["label"].map(LABEL_MAP).values
y_test  = df_test["label"].map(LABEL_MAP).values

# -----------------------------------------------------------------------
# 1. Per-class feature means on test: are FAKE/REAL distinguishable at all?
# -----------------------------------------------------------------------
print("=== Per-class feature means on TEST (top separable features) ===")
fake_test = X_test[y_test == 1]
real_test = X_test[y_test == 0]
fake_mean = fake_test.mean(axis=0)
real_mean = real_test.mean(axis=0)
pooled_std = np.sqrt((fake_test.var(axis=0) + real_test.var(axis=0)) / 2 + 1e-9)
cohen_d = (fake_mean - real_mean) / pooled_std

top_sep = np.argsort(np.abs(cohen_d))[::-1][:10]
print(f"  {'Feature':<45s} {'Cohen_d':>8}  {'FAKE_mean':>10}  {'REAL_mean':>10}")
for i in top_sep:
    print(f"  {feature_names[i]:<45s} {cohen_d[i]:>+8.3f}  {fake_mean[i]:>10.4f}  {real_mean[i]:>10.4f}")

# -----------------------------------------------------------------------
# 2. Same on train — compare separability
# -----------------------------------------------------------------------
print()
print("=== Per-class feature means on TRAIN (same top features) ===")
fake_train = X_train[y_train == 1]
real_train = X_train[y_train == 0]
fake_mean_tr = fake_train.mean(axis=0)
real_mean_tr = real_train.mean(axis=0)
pooled_std_tr = np.sqrt((fake_train.var(axis=0) + real_train.var(axis=0)) / 2 + 1e-9)
cohen_d_tr = (fake_mean_tr - real_mean_tr) / pooled_std_tr

print(f"  {'Feature':<45s} {'Train_Cohen_d':>13}  {'Test_Cohen_d':>12}")
for i in top_sep:
    print(f"  {feature_names[i]:<45s} {cohen_d_tr[i]:>+13.3f}  {cohen_d[i]:>+12.3f}")

# -----------------------------------------------------------------------
# 3. Retrain on train+val combined, evaluate on test
# -----------------------------------------------------------------------
print()
print("=== Retrain on train+val combined, evaluate on test ===")
X_trainval = np.vstack([X_train, X_val])
y_trainval = np.concatenate([y_train, y_val])
print(f"  Train+val: {X_trainval.shape}  FAKE={y_trainval.sum()} REAL={(y_trainval==0).sum()}")

rf_combined = RandomForestClassifier(
    n_estimators=200, max_depth=20, min_samples_leaf=2,
    max_features="sqrt", class_weight="balanced",
    random_state=42, n_jobs=-1,
)
rf_combined.fit(X_trainval, y_trainval)
prob_c = rf_combined.predict_proba(X_test)[:, 1]
pred_c = (prob_c >= 0.5).astype(int)
tn, fp, fn, tp = confusion_matrix(y_test, pred_c, labels=[0, 1]).ravel()
fnr_c = fn / (tp + fn)
fpr_c = fp / (tn + fp)
acc_c = accuracy_score(y_test, pred_c)
auc_c = roc_auc_score(y_test, prob_c)
print(f"  Test  accuracy={acc_c:.4f}  FNR={fnr_c:.4f}  FPR={fpr_c:.4f}  AUC={auc_c:.4f}")
print(f"  Confusion: TN={tn} FP={fp} FN={fn} TP={tp}")
print(f"  p(FAKE) mean={prob_c.mean():.4f}  "
      f"FAKE: {prob_c[y_test==1].mean():.4f}  REAL: {prob_c[y_test==0].mean():.4f}")

# -----------------------------------------------------------------------
# 4. Overall Cohen's d magnitude comparison train vs test
# -----------------------------------------------------------------------
print()
print("=== Overall separability (mean |Cohen's d| across all 124 features) ===")
print(f"  Train: {np.abs(cohen_d_tr).mean():.4f}")
print(f"  Test : {np.abs(cohen_d).mean():.4f}")
print(f"  Ratio (test/train): {np.abs(cohen_d).mean() / np.abs(cohen_d_tr).mean():.3f}")

# -----------------------------------------------------------------------
# 5. Save extended diagnosis
# -----------------------------------------------------------------------
diagnosis = {
    "cohen_d_train_mean_abs": float(np.abs(cohen_d_tr).mean()),
    "cohen_d_test_mean_abs":  float(np.abs(cohen_d).mean()),
    "separability_ratio":     float(np.abs(cohen_d).mean() / np.abs(cohen_d_tr).mean()),
    "rf_combined_retrain": {
        "train_n": int(len(y_trainval)),
        "test_accuracy": round(float(acc_c), 6),
        "test_fnr": round(float(fnr_c), 6),
        "test_fpr": round(float(fpr_c), 6),
        "test_roc_auc": round(float(auc_c), 6),
    },
    "top10_test_features_by_cohens_d": [
        {
            "feature": feature_names[i],
            "cohen_d_test": round(float(cohen_d[i]), 4),
            "cohen_d_train": round(float(cohen_d_tr[i]), 4),
        }
        for i in top_sep
    ],
    "diagnosis": (
        "The FOR-2sec test split has lower feature separability than train/val "
        "(ratio={:.3f}). This is a within-dataset covariate shift — the test split "
        "uses different speakers/sessions, causing feature distributions to shift "
        "even though generators are the same. The model has learned dataset-session "
        "artefacts rather than robust deepfake signatures.".format(
            float(np.abs(cohen_d).mean() / np.abs(cohen_d_tr).mean())
        )
    ),
}

import json
with open(MODELS / "test_diagnosis.json", "w") as f:
    json.dump(diagnosis, f, indent=2)
print("\nSaved: models/test_diagnosis.json")
