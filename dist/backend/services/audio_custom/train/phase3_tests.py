"""
ADIS Custom Audio Detector — Phase 3 Tests

Tests:
  T01: Same file → same feature vector (determinism)
  T02: Feature names/order are deterministic
  T03: Feature count is within expected range (100–130)
  T04: No forbidden metadata fields enter X
  T05: No NaN/Inf in final feature matrices (train/val/test)
  T06: Row counts match manifest split counts (accounting for failures)
  T07: No file_id appears in more than one split CSV
  T08: Feature schema is identical across train/val/test CSVs
  T09: F0 extraction handles unvoiced audio without crashing
  T10: Saved feature matrices can be reloaded successfully

Usage:
    python train/phase3_tests.py
"""

import csv
import json
import math
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

CUSTOM_DIR = Path(__file__).resolve().parents[1]
METADATA_DIR = CUSTOM_DIR / "metadata"
FEATURES_DIR = CUSTOM_DIR / "features"

sys.path.insert(0, str(CUSTOM_DIR))

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"


def load_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def feature_cols(row: dict) -> list[str]:
    """Return only the feature columns (not bookkeeping columns)."""
    skip = {"file_id", "split", "label", "path", "dataset", "speaker_id",
            "generator_id", "source_id", "for_split"}
    return sorted(k for k in row.keys() if k not in skip)


def run_tests():
    failures = 0
    results = []

    def check(tag: str, condition: bool, note: str = ""):
        nonlocal failures
        status = PASS if condition else FAIL
        if not condition:
            failures += 1
        msg = f"{status} {tag}" + (f" — {note}" if note else "")
        print(msg)
        results.append({"tag": tag, "status": status, "note": note})

    def skip(tag: str, reason: str):
        msg = f"{SKIP} {tag} — {reason}"
        print(msg)
        results.append({"tag": tag, "status": SKIP, "note": reason})

    # -----------------------------------------------------------------------
    # Load feature matrices
    # -----------------------------------------------------------------------
    train_csv = FEATURES_DIR / "train_features.csv"
    val_csv   = FEATURES_DIR / "validation_features.csv"
    test_csv  = FEATURES_DIR / "test_features.csv"
    schema_path = METADATA_DIR / "feature_schema.json"
    split_path  = METADATA_DIR / "split_A_standard.json"
    summary_path = METADATA_DIR / "feature_extraction_summary.json"

    for p in [train_csv, val_csv, test_csv, schema_path, split_path]:
        if not p.is_file():
            print(f"[ABORT] Required file missing: {p}")
            print("        Run 04_extract_features.py first.")
            return 99

    print("Loading feature CSVs...")
    train_rows = load_csv(train_csv)
    val_rows   = load_csv(val_csv)
    test_rows  = load_csv(test_csv)
    schema     = load_json(schema_path)
    split      = load_json(split_path)

    print(f"  Train: {len(train_rows)} rows")
    print(f"  Val:   {len(val_rows)} rows")
    print(f"  Test:  {len(test_rows)} rows")

    # -----------------------------------------------------------------------
    # T01: Determinism
    # -----------------------------------------------------------------------
    data_dir = CUSTOM_DIR / "data" / "for-2sec" / "for-2seconds"
    test_file = sorted((data_dir / "testing" / "real").glob("*.wav"))
    if test_file:
        test_file = test_file[0]
        from features.extractor import extract_features
        from features.schema import build_feature_names
        feat1, _ = extract_features(test_file)
        feat2, _ = extract_features(test_file)
        if feat1 is not None and feat2 is not None:
            names1 = build_feature_names(feat1)
            diffs = {k: (feat1.get(k), feat2.get(k)) for k in names1 if feat1.get(k) != feat2.get(k)}
            check("T01: Determinism (same file → same vector)", len(diffs) == 0,
                  f"differing keys: {list(diffs.keys())[:3]}")
        else:
            skip("T01", "Extraction failed on test file")
    else:
        skip("T01", "No WAV files found in testing/real")

    # -----------------------------------------------------------------------
    # T02: Feature names/order deterministic
    # -----------------------------------------------------------------------
    from features.extractor import extract_features as ef2
    from features.schema import build_feature_names as bfn
    f1, _ = ef2(test_file)
    f2, _ = ef2(test_file)
    if f1 and f2:
        names_a = bfn(f1)
        names_b = bfn(f2)
        check("T02: Feature name order deterministic", names_a == names_b,
              f"different order: {names_a[:3]} vs {names_b[:3]}")
    else:
        skip("T02", "Extraction failed")

    # -----------------------------------------------------------------------
    # T03: Feature count in range 100–130
    # -----------------------------------------------------------------------
    n_features = schema.get("n_features", 0)
    check("T03: Feature count in range [100, 130]", 100 <= n_features <= 130,
          f"n_features={n_features}")

    # -----------------------------------------------------------------------
    # T04: No forbidden metadata fields enter X
    # -----------------------------------------------------------------------
    forbidden = {"file_id", "label", "split", "path", "dataset", "speaker_id",
                 "generator_id", "source_id", "for_split", "sha256",
                 "filename", "filepath", "generator", "speaker"}
    feature_names_in_schema = set(schema.get("feature_names", []))
    leaked = forbidden & feature_names_in_schema
    check("T04: No forbidden metadata fields in feature schema", len(leaked) == 0,
          f"leaked: {leaked}")

    # -----------------------------------------------------------------------
    # T05: No NaN/Inf in feature matrices
    # -----------------------------------------------------------------------
    all_bad = []
    for split_name, rows in [("train", train_rows), ("val", val_rows), ("test", test_rows)]:
        feat_cols = feature_cols(rows[0]) if rows else []
        for row in rows:
            for col in feat_cols:
                try:
                    v = float(row[col])
                    if not math.isfinite(v):
                        all_bad.append(f"{split_name}/{row.get('file_id','?')}/{col}")
                except (TypeError, ValueError):
                    all_bad.append(f"{split_name}/{row.get('file_id','?')}/{col} (non-float)")
    check("T05: No NaN/Inf in feature matrices", len(all_bad) == 0,
          f"bad values: {len(all_bad)} (first: {all_bad[:2]})")

    # -----------------------------------------------------------------------
    # T06: Row counts match split manifest (minus failures)
    # -----------------------------------------------------------------------
    n_train_expected = split.get("n_train", 0)
    n_val_expected   = split.get("n_val", 0)
    n_test_expected  = split.get("n_test", 0)

    # Load failure count from summary
    n_failures_train = n_failures_val = n_failures_test = 0
    if summary_path.is_file():
        summary = load_json(summary_path)
        # Failures are not split by partition in summary, but we check total
        n_total_failures = summary.get("n_failed", 0)
        # If 0 failures, counts must match exactly
        if n_total_failures == 0:
            check("T06a: Train row count", len(train_rows) == n_train_expected,
                  f"got {len(train_rows)}, expected {n_train_expected}")
            check("T06b: Val row count",   len(val_rows) == n_val_expected,
                  f"got {len(val_rows)}, expected {n_val_expected}")
            check("T06c: Test row count",  len(test_rows) == n_test_expected,
                  f"got {len(test_rows)}, expected {n_test_expected}")
        else:
            # Allow rows = expected - failures
            check("T06a: Train row count approx", abs(len(train_rows) - n_train_expected) <= n_total_failures,
                  f"got {len(train_rows)}, expected ~{n_train_expected}, failures={n_total_failures}")
            check("T06b: Val row count approx",   abs(len(val_rows) - n_val_expected) <= n_total_failures,
                  f"got {len(val_rows)}, expected ~{n_val_expected}")
            check("T06c: Test row count approx",  abs(len(test_rows) - n_test_expected) <= n_total_failures,
                  f"got {len(test_rows)}, expected ~{n_test_expected}")
    else:
        skip("T06", "feature_extraction_summary.json not found")

    # -----------------------------------------------------------------------
    # T07: No file_id in multiple splits
    # -----------------------------------------------------------------------
    train_ids = {r["file_id"] for r in train_rows}
    val_ids   = {r["file_id"] for r in val_rows}
    test_ids  = {r["file_id"] for r in test_rows}
    tv_overlap = train_ids & val_ids
    tt_overlap = train_ids & test_ids
    vt_overlap = val_ids & test_ids
    check("T07a: No file_id in both train and val",  len(tv_overlap) == 0,
          f"overlap: {len(tv_overlap)}")
    check("T07b: No file_id in both train and test", len(tt_overlap) == 0,
          f"overlap: {len(tt_overlap)}")
    check("T07c: No file_id in both val and test",   len(vt_overlap) == 0,
          f"overlap: {len(vt_overlap)}")

    # -----------------------------------------------------------------------
    # T08: Feature schema identical across all three CSVs
    # -----------------------------------------------------------------------
    if train_rows and val_rows and test_rows:
        cols_train = feature_cols(train_rows[0])
        cols_val   = feature_cols(val_rows[0])
        cols_test  = feature_cols(test_rows[0])
        check("T08a: Train schema == Val schema",  cols_train == cols_val,
              f"diff: {set(cols_train) ^ set(cols_val)}")
        check("T08b: Train schema == Test schema", cols_train == cols_test,
              f"diff: {set(cols_train) ^ set(cols_test)}")
    else:
        skip("T08", "Empty CSV(s)")

    # -----------------------------------------------------------------------
    # T09: F0 extraction handles unvoiced/silent audio
    # -----------------------------------------------------------------------
    from features.extractor import _pitch_features
    import numpy as np
    # Test 1: pure silence → should not crash, voiced_ratio = 0
    silence = np.zeros(32000, dtype=np.float32)
    pf = _pitch_features(silence, 16000)
    check("T09a: Silence handled without crash", True)
    check("T09b: Silence voiced_ratio = 0", pf.get("voiced_ratio", -1) == 0.0,
          f"voiced_ratio={pf.get('voiced_ratio')}")
    check("T09c: Silence f0_mean = 0", pf.get("f0_mean", -1) == 0.0,
          f"f0_mean={pf.get('f0_mean')}")

    # -----------------------------------------------------------------------
    # T10: Feature matrices can be reloaded
    # -----------------------------------------------------------------------
    for split_name, csv_path in [("train", train_csv), ("val", val_csv), ("test", test_csv)]:
        try:
            rows = load_csv(csv_path)
            check(f"T10{split_name[0]}: {split_name}_features.csv reloads successfully",
                  len(rows) > 0, f"rows={len(rows)}")
        except Exception as e:
            check(f"T10{split_name[0]}: {split_name}_features.csv reloads", False,
                  f"error: {e}")

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    total = len(results)
    passed   = sum(1 for r in results if r["status"] == PASS)
    skipped  = sum(1 for r in results if r["status"] == SKIP)
    failed_l = [r for r in results if r["status"] == FAIL]

    print(f"\n{'='*60}")
    print(f"PHASE 3 TESTS: {passed} passed / {failures} failed / {skipped} skipped")
    print(f"{'='*60}")
    if failed_l:
        print("FAILED:")
        for r in failed_l:
            print(f"  {r['tag']}: {r['note']}")

    return failures


if __name__ == "__main__":
    failures = run_tests()
    sys.exit(0 if failures == 0 else 1)
