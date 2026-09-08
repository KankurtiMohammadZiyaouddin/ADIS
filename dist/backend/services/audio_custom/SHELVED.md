# Custom Acoustic Detector — Development Record

## Status: SHELVED (not integrated into ADIS)

**Decision date:** Phase 8 completion  
**Decision:** Skip custom RF detector. Ship with YAMNet only.

---

## What was built

A complete acoustic feature pipeline for deepfake audio detection:

- **17,870 files** from FOR-2sec dataset extracted (100% success, 0 failures)
- **124 acoustic features** per file: MFCC 1–13 + deltas + delta-deltas, spectral contrast (7 bands), spectral centroid/bandwidth/rolloff/flatness, band energy ratios, RMS, ZCR, F0/voicing
- **Logistic Regression** (baseline) + **Random Forest** (primary, 200 trees, max_depth=20)
- Train/val performance: RF val accuracy 99.72%, FNR 0.14%, ROC-AUC 0.9996
- Phase 5 tuning: threshold sweep, RF grid search (18 configs), LR C sweep

---

## Why it was not deployed

### Root cause: FOR-2sec codec confound

The FOR-2sec dataset has a structural flaw: training FAKE files are MP3-sourced
(`file10005.mp3.wav_16k...`) while test FAKE files are WAV-sourced
(`file100.wav_16k...`). The classifier learned MP3 codec artefacts, not TTS
synthesis signatures.

**Evidence:**
- Val accuracy 99.72% → Test accuracy 49.17% (near-random)
- Test ROC-AUC 0.4523 (worse than coin flip)
- `mfcc_delta_4_std` Cohen's d: +0.89 in train → −2.20 in test (direction reversal)
- CMS (Cepstral Mean Subtraction) applied — did not fix it; confound pervades variance features too

### What would fix it

1. **Data augmentation:** MP3-encode training FAKE WAVs at multiple bitrates, retrain
2. **Alternative dataset:** ASVspoof 2019 LA or In-The-Wild (no codec confound)
3. **Feature subset:** Exclude codec-sensitive features (MFCC means, spectral flatness mean)

None of these were pursued — cost/time not justified when YAMNet already works.

---

## Forensic integrity note

The custom detector was **never integrated into ADIS**. No production file was
modified during this development work. All changes are confined to:

```
dist/backend/services/audio_custom/   ← entirely new, not imported anywhere
```

The existing 22-test suite passes unchanged. YAMNet remains the sole audio
detector in production.

---

## Artefacts retained (for future resumption)

| Path | Description |
|------|-------------|
| `features/extractor.py` | 124-feature extractor with CMS support |
| `features/schema.py` | Feature schema + exclusion rules |
| `models/random_forest.joblib` | Phase 5 best RF (val-only, DO NOT deploy) |
| `models/scaler.joblib` | StandardScaler fit on train |
| `models/training_summary.json` | Phase 4 metrics |
| `models/tuning_summary.json` | Phase 5 sweep results |
| `models/test_evaluation.json` | Phase 6 test results + diagnosis |
| `models/test_diagnosis.json` | Codec confound diagnosis detail |
| `models/cms/` | Phase 8 CMS retrain (also failed) |
| `metadata/` | Manifests, splits, feature schema |

All model files are **not connected to any ADIS endpoint**. They exist only as
research artefacts.

---

## Resumption path

To revisit this work with a better dataset:

1. Download ASVspoof 2019 LA (`train`, `dev`, `eval` splits — codec-consistent)
2. Run `train/03_build_for_manifest.py` adapted for ASVspoof file structure
3. Re-run `train/04_extract_features.py` (CMS enabled by default)
4. Re-run `train/05_train_classifiers.py`
5. Validate test ROC-AUC ≥ 0.80 before Phase 9 integration
