# ADIS Custom Audio Deepfake Detector

## Purpose

Independent acoustic-feature-based detector. Does NOT use YAMNet embeddings.
Designed to complement the existing Deepfake-YamNet detector.

## Architecture

```
Audio File
    ↓
Preprocessing (mono, 16 kHz, float32)
    ↓
Windowed Feature Extraction (spectral + temporal + MFCC + pitch/voicing)
    ↓
File-level Aggregation
    ↓
StandardScaler (fitted on train only)
    ↓
Logistic Regression (baseline) / Random Forest (primary)
    ↓
FAKE / REAL
```

## Directory Structure

```
audio_custom/
├── data/
│   ├── in_the_wild/          # In The Wild (Kaggle CC BY 4.0) — NOT committed
│   │   ├── fake/
│   │   └── real/
│   └── rvcbench/             # RVCBench (HuggingFace CC0) — NOT committed
├── features/                 # Extracted feature matrices — NOT committed
├── models/                   # Trained model artifacts (joblib) — committed if small
├── evaluation/               # Evaluation results (JSON/CSV)
├── metadata/                 # Manifests, splits, configs
├── tests/
│   └── unseen_gemini/        # Gemini test sample (unseen generator) — NOT committed
└── train/                    # Training pipeline scripts
```

## Leakage Policy

- Splits happen at FILE level before any feature extraction.
- Where speaker IDs are known, splits are GROUP-AWARE (no speaker appears in both train and test).
- Generator holdout: at least one synthetic generator is held out entirely from training.
- Gemini sample: reserved exclusively as unseen-generator diagnostic. Never used for training or tuning.

## Training Datasets

| Dataset       | Source                                             | License    | Role          |
|---------------|----------------------------------------------------|------------|---------------|
| In The Wild   | kaggle: abdallamohamed312/in-the-wild-audio-deepfake | CC BY 4.0  | REAL + FAKE   |
| RVCBench      | huggingface: Nanboy/RVCBench                       | CC0 1.0    | REAL + FAKE   |

## Non-negotiable Rules

1. No hardcoded confidence values.
2. No fabricated metrics.
3. No test-set leakage into preprocessing or scaling.
4. No Gemini samples in training.
5. No modification of the existing Deepfake-YamNet detector.
