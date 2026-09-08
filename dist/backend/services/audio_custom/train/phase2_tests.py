"""
ADIS Custom Audio Detector — Phase 2 Validation Tests

Verifies:
  T01: acquisition_manifest.csv exists and is non-empty
  T02: dataset_manifest.csv exists and is non-empty
  T03: No duplicate file_ids in manifest
  T04: All labels are REAL or FAKE
  T05: split_A_standard.json exists with required keys
  T06: Split A — no file overlap between train and test
  T07: Split A — no file overlap between train and val
  T08: Split A — no speaker overlap between train and test (where known)
  T09: Split B json exists
  T10: Split B — no file overlap between train and test
  T11: Split B — holdout generator not present in training data
  T12: dataset_statistics.json exists with valid counts
  T13: unseen_gemini directory exists (Gemini file may be absent — that is OK)
  T14: No NaN or 'None' strings in file_id, label, path columns
  T15: Split A train+val+test = total manifest records

Usage:
    python train/phase2_tests.py
"""

import csv
import json
import sys
from pathlib import Path

CUSTOM_DIR = Path(__file__).resolve().parents[1]
METADATA_DIR = CUSTOM_DIR / "metadata"
TESTS_DIR    = CUSTOM_DIR / "tests"

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"
WARN = "[WARN]"


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def load_csv(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run_tests():
    results = []
    failures = 0

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
    # T01: acquisition_manifest exists and non-empty
    # -----------------------------------------------------------------------
    acq_path = METADATA_DIR / "acquisition_manifest.csv"
    check("T01: acquisition_manifest.csv exists", acq_path.is_file(),
          f"path={acq_path}")

    acq_records = []
    if acq_path.is_file():
        acq_records = load_csv(acq_path)
        check("T01b: acquisition_manifest non-empty", len(acq_records) > 0,
              f"found {len(acq_records)} rows")

    # -----------------------------------------------------------------------
    # T02: dataset_manifest exists
    # -----------------------------------------------------------------------
    man_path = METADATA_DIR / "dataset_manifest.csv"
    check("T02: dataset_manifest.csv exists", man_path.is_file())

    records = []
    if man_path.is_file():
        records = load_csv(man_path)
        check("T02b: dataset_manifest non-empty", len(records) > 0,
              f"found {len(records)} rows")

    if not records:
        print(f"\n[ABORT] No manifest records. Skipping dependent tests.")
        print(f"\nResults: {failures} failures out of {len(results)} tests.")
        return failures

    # -----------------------------------------------------------------------
    # T03: No duplicate file_ids
    # -----------------------------------------------------------------------
    fids = [r["file_id"] for r in records]
    dup_count = len(fids) - len(set(fids))
    check("T03: No duplicate file_ids", dup_count == 0,
          f"duplicates: {dup_count}")

    # -----------------------------------------------------------------------
    # T04: All labels are REAL or FAKE
    # -----------------------------------------------------------------------
    invalid_labels = [r["file_id"] for r in records if r.get("label") not in {"REAL", "FAKE"}]
    check("T04: All labels are REAL or FAKE", len(invalid_labels) == 0,
          f"invalid: {invalid_labels[:5]}")

    # -----------------------------------------------------------------------
    # T14: No NaN or 'None' strings in critical columns
    # -----------------------------------------------------------------------
    bad_fid = [r for r in records if not r.get("file_id") or r["file_id"] in {"None", "nan", ""}]
    bad_lbl = [r for r in records if r.get("label") in {"None", "nan", ""}]
    bad_pth = [r for r in records if not r.get("path") or r["path"] in {"None", "nan", ""}]
    check("T14a: No empty/null file_ids", len(bad_fid) == 0, f"count: {len(bad_fid)}")
    check("T14b: No empty/null labels",  len(bad_lbl) == 0, f"count: {len(bad_lbl)}")
    check("T14c: No empty/null paths",   len(bad_pth) == 0, f"count: {len(bad_pth)}")

    # -----------------------------------------------------------------------
    # T05: split_A json exists with required keys
    # -----------------------------------------------------------------------
    split_A_path = METADATA_DIR / "split_A_standard.json"
    check("T05: split_A_standard.json exists", split_A_path.is_file())

    split_A = {}
    if split_A_path.is_file():
        split_A = load_json(split_A_path)
        required_keys = {"train_ids", "val_ids", "test_ids", "n_train", "n_val", "n_test"}
        missing_keys = required_keys - set(split_A.keys())
        check("T05b: Split A has required keys", len(missing_keys) == 0,
              f"missing: {missing_keys}")

    # -----------------------------------------------------------------------
    # T06: Split A — no file overlap train/test
    # -----------------------------------------------------------------------
    if split_A and "train_ids" in split_A:
        train_set = set(split_A["train_ids"])
        val_set   = set(split_A["val_ids"])
        test_set  = set(split_A["test_ids"])

        tt_overlap = train_set & test_set
        check("T06: Split A train/test no file overlap", len(tt_overlap) == 0,
              f"overlap count: {len(tt_overlap)}")

        # -----------------------------------------------------------------------
        # T07: Split A — no file overlap train/val
        # -----------------------------------------------------------------------
        tv_overlap = train_set & val_set
        check("T07: Split A train/val no file overlap", len(tv_overlap) == 0,
              f"overlap count: {len(tv_overlap)}")

        # -----------------------------------------------------------------------
        # T08: Split A — no speaker overlap train/test (where known)
        # -----------------------------------------------------------------------
        fid_to_record = {r["file_id"]: r for r in records}

        def spks(id_set):
            return {fid_to_record[fid]["speaker_id"]
                    for fid in id_set
                    if fid in fid_to_record and fid_to_record[fid]["speaker_id"] != "unknown"}

        train_spks = spks(train_set)
        test_spks  = spks(test_set)
        spk_overlap = train_spks & test_spks
        if train_spks or test_spks:
            check("T08: Split A no speaker overlap train/test", len(spk_overlap) == 0,
                  f"overlapping speakers: {sorted(spk_overlap)[:5]}")
        else:
            skip("T08: Split A no speaker overlap", "All speaker_ids are 'unknown' — cannot check")

        # -----------------------------------------------------------------------
        # T15: Split A train+val+test = total manifest records
        # -----------------------------------------------------------------------
        total_in_splits = len(train_set) + len(val_set) + len(test_set)
        total_in_manifest = len(records)
        check("T15: Split A total = manifest total", total_in_splits == total_in_manifest,
              f"splits={total_in_splits}, manifest={total_in_manifest}")

    else:
        skip("T06", "Split A not loaded")
        skip("T07", "Split A not loaded")
        skip("T08", "Split A not loaded")
        skip("T15", "Split A not loaded")

    # -----------------------------------------------------------------------
    # T09: split_B json exists
    # -----------------------------------------------------------------------
    split_B_path = METADATA_DIR / "split_B_generator_holdout.json"
    check("T09: split_B_generator_holdout.json exists", split_B_path.is_file())

    split_B = {}
    if split_B_path.is_file():
        split_B = load_json(split_B_path)

    # -----------------------------------------------------------------------
    # T10: Split B — no file overlap train/test
    # -----------------------------------------------------------------------
    if split_B.get("status") in ("READY", "APPROXIMATE") and "train_ids" in split_B:
        b_train_set = set(split_B["train_ids"])
        b_test_set  = set(split_B["test_ids"])
        b_overlap   = b_train_set & b_test_set
        check("T10: Split B train/test no file overlap", len(b_overlap) == 0,
              f"overlap count: {len(b_overlap)}")

        # -----------------------------------------------------------------------
        # T11: Split B — generator leakage check
        # -----------------------------------------------------------------------
        status = split_B.get("status")
        if status == "APPROXIMATE":
            skip("T11", f"Split B is APPROXIMATE — per-file generator labels not available in FOR-2sec")
        else:
            holdout_gen = split_B.get("holdout_generator", "")
            fid_to_record = {r["file_id"]: r for r in records}
            holdout_in_train = [
                fid for fid in b_train_set
                if fid in fid_to_record and fid_to_record[fid].get("generator_id") == holdout_gen
            ]
            check("T11: Split B holdout generator not in train", len(holdout_in_train) == 0,
                  f"holdout={holdout_gen}, found in train: {len(holdout_in_train)}")
    elif split_B.get("status") == "SKIPPED":
        skip("T10", f"Split B skipped: {split_B.get('reason', '')}")
        skip("T11", f"Split B skipped: {split_B.get('reason', '')}")
    else:
        skip("T10", "Split B not available")
        skip("T11", "Split B not available")

    # -----------------------------------------------------------------------
    # T12: dataset_statistics.json exists with valid counts
    # -----------------------------------------------------------------------
    stats_path = METADATA_DIR / "dataset_statistics.json"
    check("T12: dataset_statistics.json exists", stats_path.is_file())
    if stats_path.is_file():
        stats = load_json(stats_path)
        has_counts = "n_real" in stats and "n_fake" in stats
        check("T12b: Statistics has REAL/FAKE counts", has_counts,
              f"n_real={stats.get('n_real')}, n_fake={stats.get('n_fake')}")

    # -----------------------------------------------------------------------
    # T13: unseen_gemini directory exists
    # -----------------------------------------------------------------------
    gemini_dir = TESTS_DIR / "unseen_gemini"
    check("T13: unseen_gemini directory exists", gemini_dir.is_dir())

    # Check if Gemini file is present (not required — just report)
    gemini_files = list(gemini_dir.glob("*.mp3")) + list(gemini_dir.glob("*.wav"))
    if gemini_files:
        print(f"[INFO] Gemini test file(s) found: {[f.name for f in gemini_files]}")
    else:
        print(f"[INFO] No Gemini test file in {gemini_dir} — evaluation pending.")

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    total_tests = len(results)
    passed = sum(1 for r in results if r["status"] == PASS)
    failed_list = [r for r in results if r["status"] == FAIL]
    skipped = sum(1 for r in results if r["status"] == SKIP)

    print(f"\n{'='*60}")
    print(f"PHASE 2 TESTS: {passed} passed / {failures} failed / {skipped} skipped")
    print(f"{'='*60}")
    if failed_list:
        print("FAILED TESTS:")
        for r in failed_list:
            print(f"  {r['tag']}: {r['note']}")

    return failures


if __name__ == "__main__":
    failures = run_tests()
    sys.exit(0 if failures == 0 else 1)
