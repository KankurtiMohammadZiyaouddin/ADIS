"""
ADIS Custom Audio Detector — Phase 3
Step 4: Feature Extraction Pipeline

Reads:  metadata/dataset_manifest.csv
        metadata/split_A_standard.json
Writes: features/train_features.csv
        features/validation_features.csv
        features/test_features.csv
        metadata/feature_schema.json
        metadata/feature_extraction_summary.json
        metadata/feature_failures.csv
        metadata/feature_statistics.csv

Leakage guarantee:
  - Features are extracted per-file using only the audio waveform.
  - No filename, path, label, or metadata enters the feature vector.
  - Split boundaries from Phase 2 are preserved exactly.
  - 1 file → 1 row; no window overlap across files.

Usage:
    python train/04_extract_features.py [--max-failures-pct FLOAT] [--dry-run]

Options:
    --max-failures-pct  Abort if failure rate exceeds this % (default: 5.0)
    --dry-run           Extract only first 20 files per split for testing
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
import warnings
from collections import defaultdict
from pathlib import Path

# Suppress verbose deprecation warnings from librosa/numpy during bulk extraction
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*yin.*")

CUSTOM_DIR = Path(__file__).resolve().parents[1]
METADATA_DIR = CUSTOM_DIR / "metadata"
FEATURES_DIR = CUSTOM_DIR / "features"
FEATURES_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(CUSTOM_DIR))
from features.extractor import extract_features, EXTRACTOR_CONFIG
from features.schema import (
    build_feature_names,
    feature_dict_to_vector,
    validate_feature_vector,
    EXCLUDED_KEYS,
)

import librosa
import numpy as np

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_manifest(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_split(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def build_id_to_record(records: list[dict]) -> dict:
    return {r["file_id"]: r for r in records}


# ---------------------------------------------------------------------------
# Extraction per split
# ---------------------------------------------------------------------------

def extract_split(
    records: list[dict],
    split_name: str,
    feature_names: list[str] | None,
    max_failures_pct: float,
    dry_run: bool,
) -> tuple[list[dict], list[dict], list[str]]:
    """
    Extract features for all records in a split.

    Returns:
        rows          — list of row dicts (including file_id, label, feature values)
        failure_rows  — list of failure dicts
        feature_names — (possibly first-initialized from this split)
    """
    rows = []
    failure_rows = []
    n = len(records)
    if dry_run:
        records = records[:20]
        n = len(records)
        print(f"  [DRY RUN] Processing only {n} files for {split_name}")

    t0 = time.time()
    print(f"\n[{split_name}] Extracting features for {n} files...")

    for i, rec in enumerate(records):
        fid   = rec["file_id"]
        label = rec["label"]
        path  = rec["path"]

        if i % 500 == 0 and i > 0:
            elapsed = time.time() - t0
            rate = i / elapsed
            remaining = (n - i) / max(rate, 1e-6)
            print(f"  [{i}/{n}] elapsed={elapsed:.0f}s  rate={rate:.1f}/s  ETA={remaining:.0f}s")

        # Check path exists
        if not Path(path).is_file():
            failure_rows.append({
                "file_id": fid,
                "split": split_name,
                "label": label,
                "path": path,
                "error_type": "file_not_found",
                "error_message": f"Path does not exist: {path}",
            })
            continue

        # Extract features
        feat, err = extract_features(path)

        if feat is None:
            failure_rows.append({
                "file_id": fid,
                "split": split_name,
                "label": label,
                "path": path,
                "error_type": "extraction_error",
                "error_message": str(err)[:200],
            })
            continue

        # First successful extraction: initialize feature_names
        if feature_names is None:
            feature_names = build_feature_names(feat)

        # Build row: bookkeeping columns + feature values
        vec = feature_dict_to_vector(feat, feature_names)

        # Check for NaN/Inf
        is_valid, bad_keys = validate_feature_vector(vec, feature_names)
        if not is_valid:
            failure_rows.append({
                "file_id": fid,
                "split": split_name,
                "label": label,
                "path": path,
                "error_type": "nan_inf_in_features",
                "error_message": f"Bad features: {bad_keys[:5]}",
            })
            continue

        row = {"file_id": fid, "split": split_name, "label": label}
        for k, v in zip(feature_names, vec):
            row[k] = v
        rows.append(row)

    elapsed = time.time() - t0
    fail_pct = len(failure_rows) / max(n, 1) * 100

    print(f"  [{split_name}] Done: {len(rows)} success, {len(failure_rows)} failed ({fail_pct:.2f}%) in {elapsed:.1f}s")

    # Stop condition: too many failures
    if fail_pct > max_failures_pct:
        print(f"\n[ERROR] Failure rate {fail_pct:.1f}% exceeds limit {max_failures_pct:.1f}%.")
        print("  Aborting to prevent training on degraded dataset.")
        sys.exit(1)

    return rows, failure_rows, feature_names


# ---------------------------------------------------------------------------
# Feature statistics per column
# ---------------------------------------------------------------------------

def compute_feature_statistics(
    all_rows: list[dict],
    feature_names: list[str],
) -> list[dict]:
    """Per-feature: min, max, mean, std, median, variance, n_unique, n_zero, n_nan."""
    stats = []
    n = len(all_rows)
    for fname in feature_names:
        vals = []
        for row in all_rows:
            v = row.get(fname, None)
            if v is not None:
                try:
                    vals.append(float(v))
                except (TypeError, ValueError):
                    pass

        vals_arr = np.array(vals, dtype=np.float64)
        finite = vals_arr[np.isfinite(vals_arr)]
        n_nan_inf = len(vals_arr) - len(finite)
        n_unique = len(set(finite.tolist())) if len(finite) > 0 else 0
        n_zero   = int(np.sum(finite == 0.0)) if len(finite) > 0 else 0

        stats.append({
            "feature_name": fname,
            "n_samples": n,
            "n_nan_inf": n_nan_inf,
            "n_unique": n_unique,
            "n_zero": n_zero,
            "min":      float(np.min(finite))    if len(finite) > 0 else None,
            "max":      float(np.max(finite))    if len(finite) > 0 else None,
            "mean":     float(np.mean(finite))   if len(finite) > 0 else None,
            "std":      float(np.std(finite))    if len(finite) > 0 else None,
            "median":   float(np.median(finite)) if len(finite) > 0 else None,
            "variance": float(np.var(finite))    if len(finite) > 0 else None,
        })
    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ADIS — Feature Extraction Pipeline")
    parser.add_argument("--max-failures-pct", type=float, default=5.0,
                        help="Abort if failure rate exceeds this percentage (default: 5.0)")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Extract only first 20 files per split for testing")
    args = parser.parse_args()

    t_start = time.time()

    # Load manifest and split
    manifest = METADATA_DIR / "dataset_manifest.csv"
    split_file = METADATA_DIR / "split_A_standard.json"

    if not manifest.is_file():
        print(f"[ERROR] Manifest not found: {manifest}")
        sys.exit(1)
    if not split_file.is_file():
        print(f"[ERROR] Split file not found: {split_file}")
        sys.exit(1)

    print(f"[Setup] Loading manifest and split...")
    records = load_manifest(manifest)
    split   = load_split(split_file)

    id_to_rec = build_id_to_record(records)

    train_ids = set(split["train_ids"])
    val_ids   = set(split["val_ids"])
    test_ids  = set(split["test_ids"])

    train_recs = [id_to_rec[fid] for fid in sorted(train_ids) if fid in id_to_rec]
    val_recs   = [id_to_rec[fid] for fid in sorted(val_ids)   if fid in id_to_rec]
    test_recs  = [id_to_rec[fid] for fid in sorted(test_ids)  if fid in id_to_rec]

    print(f"[Setup] Train={len(train_recs)}, Val={len(val_recs)}, Test={len(test_recs)}")

    all_failure_rows = []
    feature_names = None
    all_rows = []

    # Extract each split in order
    for split_name, recs in [("train", train_recs), ("validation", val_recs), ("test", test_recs)]:
        rows, failures, feature_names = extract_split(
            recs, split_name, feature_names, args.max_failures_pct, args.dry_run
        )
        all_rows.extend(rows)
        all_failure_rows.extend(failures)

        # Write split CSV immediately (memory-efficient)
        out_path = FEATURES_DIR / f"{split_name}_features.csv"
        if rows:
            fieldnames = list(rows[0].keys())
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"  Written: {out_path} ({len(rows)} rows, {len(feature_names)} features)")
        else:
            print(f"  [WARN] No rows for {split_name} — CSV not written.")

    # Save feature schema
    if feature_names:
        schema_path = METADATA_DIR / "feature_schema.json"
        schema = {
            "feature_names": feature_names,
            "n_features": len(feature_names),
            "extractor_version": EXTRACTOR_CONFIG["extractor_version"],
            "excluded_keys": sorted(EXCLUDED_KEYS),
            "notes": [
                "Features are ordered alphabetically.",
                "Keys starting with '_' are diagnostic and excluded from X.",
                "'low_energy_threshold_hz', 'f0_n_voiced_frames' are also excluded.",
                "label, file_id, split, path are bookkeeping columns — never enter X.",
            ],
        }
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=2)
        print(f"\n[Schema] Saved: {schema_path}")

    # Save failures
    failures_path = METADATA_DIR / "feature_failures.csv"
    if all_failure_rows:
        fieldnames = ["file_id", "split", "label", "path", "error_type", "error_message"]
        with open(failures_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_failure_rows)
        print(f"[Failures] {len(all_failure_rows)} failures written to {failures_path}")
    else:
        # Write empty file with headers
        with open(failures_path, "w", newline="", encoding="utf-8") as f:
            f.write("file_id,split,label,path,error_type,error_message\n")
        print(f"[Failures] 0 failures.")

    # Feature statistics (on training data only — avoid test set influence)
    train_rows = [r for r in all_rows if r.get("split") == "train"]
    print(f"\n[Stats] Computing feature statistics on training set ({len(train_rows)} rows)...")
    if train_rows and feature_names:
        stats = compute_feature_statistics(train_rows, feature_names)
        stats_path = METADATA_DIR / "feature_statistics.csv"
        with open(stats_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = list(stats[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(stats)
        print(f"  Saved: {stats_path}")

        # Identify constant / near-constant features
        n_total_feats = len(feature_names)
        constant_feats    = [s["feature_name"] for s in stats if s["n_unique"] is not None and s["n_unique"] <= 1]
        near_const_feats  = [s["feature_name"] for s in stats
                             if s["variance"] is not None and 0 < s["variance"] < 1e-8]
        any_nan_inf_feats = [s["feature_name"] for s in stats if s["n_nan_inf"] and s["n_nan_inf"] > 0]

        print(f"  Total features: {n_total_feats}")
        print(f"  Constant features (0 or 1 unique value): {len(constant_feats)}")
        if constant_feats:
            print(f"    {constant_feats[:10]}")
        print(f"  Near-constant features (variance < 1e-8): {len(near_const_feats)}")
        if near_const_feats:
            print(f"    {near_const_feats[:10]}")
        print(f"  Features with any NaN/Inf: {len(any_nan_inf_feats)}")
        if any_nan_inf_feats:
            print(f"    {any_nan_inf_feats[:10]}")
    else:
        stats = []
        constant_feats = []
        near_const_feats = []
        any_nan_inf_feats = []

    # Class balance check
    print(f"\n[Balance] Class balance check:")
    for split_name in ["train", "validation", "test"]:
        split_rows = [r for r in all_rows if r.get("split") == split_name]
        n_real = sum(1 for r in split_rows if r.get("label") == "REAL")
        n_fake = sum(1 for r in split_rows if r.get("label") == "FAKE")
        total  = len(split_rows)
        print(f"  {split_name:12s}: {total:5d} total | REAL={n_real} FAKE={n_fake} | ratio={n_fake/max(total,1):.3f}")

    # Summary JSON
    t_total = time.time() - t_start
    import platform
    summary = {
        "extraction_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "python_version": sys.version,
        "librosa_version": librosa.__version__,
        "numpy_version": np.__version__,
        "extractor_version": EXTRACTOR_CONFIG["extractor_version"],
        "extractor_config": EXTRACTOR_CONFIG,
        "feature_count": len(feature_names) if feature_names else 0,
        "feature_names": feature_names or [],
        "n_total_files_attempted": len(train_recs) + len(val_recs) + len(test_recs),
        "n_successful": len(all_rows),
        "n_failed": len(all_failure_rows),
        "failure_rate_pct": round(len(all_failure_rows) / max(len(train_recs) + len(val_recs) + len(test_recs), 1) * 100, 4),
        "split_counts": {
            "train": len([r for r in all_rows if r.get("split") == "train"]),
            "validation": len([r for r in all_rows if r.get("split") == "validation"]),
            "test": len([r for r in all_rows if r.get("split") == "test"]),
        },
        "class_balance": {
            s: {
                "REAL": sum(1 for r in all_rows if r.get("split") == s and r.get("label") == "REAL"),
                "FAKE": sum(1 for r in all_rows if r.get("split") == s and r.get("label") == "FAKE"),
            }
            for s in ["train", "validation", "test"]
        },
        "constant_features": constant_feats,
        "near_constant_features": near_const_feats,
        "features_with_nan_inf": any_nan_inf_feats,
        "total_extraction_time_s": round(t_total, 1),
        "dry_run": args.dry_run,
        "preprocessing": {
            "target_sr_hz": EXTRACTOR_CONFIG["target_sr"],
            "mono": EXTRACTOR_CONFIG["mono"],
            "n_fft": EXTRACTOR_CONFIG["n_fft"],
            "hop_length": EXTRACTOR_CONFIG["hop_length"],
            "n_mfcc": EXTRACTOR_CONFIG["n_mfcc"],
            "n_mels": EXTRACTOR_CONFIG["n_mels"],
            "n_spectral_contrast_bands": EXTRACTOR_CONFIG["n_bands"],
            "pitch_fmin_hz": EXTRACTOR_CONFIG["fmin_pitch"],
            "pitch_fmax_hz": EXTRACTOR_CONFIG["fmax_pitch"],
            "low_energy_threshold_factor": EXTRACTOR_CONFIG["low_energy_threshold_factor"],
        },
        "hnr_status": "NOT INCLUDED — no reliable HNR in existing environment without extra packages",
    }
    summary_path = METADATA_DIR / "feature_extraction_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n[Summary] Saved: {summary_path}")

    print(f"\n{'='*60}")
    print("FEATURE EXTRACTION COMPLETE")
    print(f"{'='*60}")
    print(f"Files processed:    {len(all_rows)}/{len(train_recs)+len(val_recs)+len(test_recs)}")
    print(f"Failed:             {len(all_failure_rows)}")
    print(f"Feature count:      {len(feature_names) if feature_names else 0}")
    print(f"Constant features:  {len(constant_feats)}")
    print(f"Near-const feats:   {len(near_const_feats)}")
    print(f"NaN/Inf features:   {len(any_nan_inf_feats)}")
    print(f"Total time:         {t_total:.1f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
