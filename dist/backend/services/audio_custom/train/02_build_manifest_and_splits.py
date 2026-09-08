"""
ADIS Custom Audio Detector — Phase 2
Step 2: Build Manifest & Leakage-Safe Splits

Reads: metadata/acquisition_manifest.csv
Writes:
  metadata/dataset_manifest.csv        — cleaned, verified manifest
  metadata/split_A_standard.json       — 70/15/15 file-level group-aware split
  metadata/split_B_generator_holdout.json — generator holdout split
  metadata/split_summary.json          — validation report

LEAKAGE RULES ENFORCED:
  1. File leakage:     A file can appear in exactly one split partition.
  2. Speaker leakage:  Where speaker_id != 'unknown', a speaker cannot appear
                       in both train and test.
  3. Generator leakage (Split B): A held-out generator appears ONLY in the
                       test partition of Split B.

Usage:
    python train/02_build_manifest_and_splits.py [--seed INT] [--holdout-generator ID]
"""

import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

CUSTOM_DIR = Path(__file__).resolve().parents[1]
METADATA_DIR = CUSTOM_DIR / "metadata"

RANDOM_SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO   = 0.15
TEST_RATIO  = 0.15


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_manifest(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save_manifest(records: list[dict], path: Path):
    if not records:
        print(f"[WARN] No records to save to {path}")
        return
    fieldnames = list(records[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


# ---------------------------------------------------------------------------
# Manifest verification
# ---------------------------------------------------------------------------

def verify_manifest(records: list[dict]) -> dict:
    """
    Check for:
      - Duplicate file_ids
      - Missing labels
      - Invalid labels
      - Missing paths
      - Files that don't exist on disk
    Returns a verification report dict.
    """
    issues = []
    seen_ids = {}
    missing_paths = []
    invalid_labels = []
    label_counts = defaultdict(int)

    for r in records:
        fid = r.get("file_id", "")
        label = r.get("label", "")
        path = r.get("path", "")

        # Duplicate IDs
        if fid in seen_ids:
            issues.append(f"Duplicate file_id: {fid}")
        else:
            seen_ids[fid] = True

        # Label validity
        if label not in {"REAL", "FAKE"}:
            invalid_labels.append(fid)
            issues.append(f"Invalid label '{label}' for file_id {fid}")
        else:
            label_counts[label] += 1

        # Path existence
        if path and not Path(path).is_file():
            missing_paths.append(path)

    report = {
        "total_records": len(records),
        "n_real": label_counts["REAL"],
        "n_fake": label_counts["FAKE"],
        "duplicate_ids": len(issues),
        "missing_paths": len(missing_paths),
        "invalid_labels": len(invalid_labels),
        "issues": issues[:20],  # cap for readability
    }
    return report


# ---------------------------------------------------------------------------
# Group assembly
# ---------------------------------------------------------------------------

def build_groups(records: list[dict]) -> dict:
    """
    Build split groups.

    Priority:
      1. If speaker_id is known → group by speaker_id
      2. Else if source_id is known → group by source_id (keeps same-source files together)
      3. Else → group by file_id (each file is its own group, still file-safe)

    Returns: {group_key: [record, ...]}
    """
    groups = defaultdict(list)
    for r in records:
        spk = r.get("speaker_id", "unknown")
        src = r.get("source_id", "unknown")
        fid = r.get("file_id", "")

        if spk != "unknown":
            group_key = f"spk_{spk}"
        elif src != "unknown":
            # Group by source+dataset so ITW files from different parts stay together
            group_key = f"src_{src}"
        else:
            # Fallback: each file is its own group (no speaker leakage possible)
            group_key = f"file_{fid}"

        groups[group_key].append(r)

    return dict(groups)


# ---------------------------------------------------------------------------
# Split A: Standard group-aware split
# ---------------------------------------------------------------------------

def split_A_standard(records: list[dict], seed: int) -> dict:
    """
    70/15/15 stratified group split.

    Strategy:
      1. Separate FAKE and REAL records.
      2. Build groups independently for FAKE and REAL.
      3. Split groups (not files) into 70/15/15.
      4. Assign all files in each group to the same partition.

    This ensures:
      - Speaker groups never span train/test.
      - Approximate label balance maintained across splits.
    """
    import random as _random
    rng = _random.Random(seed)

    def _split_groups(group_dict: dict) -> tuple[list, list, list]:
        keys = sorted(group_dict.keys())
        rng.shuffle(keys)
        n = len(keys)
        n_train = max(1, int(n * TRAIN_RATIO))
        n_val = max(1, int(n * VAL_RATIO))
        train_keys = keys[:n_train]
        val_keys = keys[n_train:n_train + n_val]
        test_keys = keys[n_train + n_val:]
        return train_keys, val_keys, test_keys

    fake_records = [r for r in records if r["label"] == "FAKE"]
    real_records = [r for r in records if r["label"] == "REAL"]

    fake_groups = build_groups(fake_records)
    real_groups = build_groups(real_records)

    print(f"[Split A] FAKE groups: {len(fake_groups)}, REAL groups: {len(real_groups)}")

    fake_train_keys, fake_val_keys, fake_test_keys = _split_groups(fake_groups)
    real_train_keys, real_val_keys, real_test_keys = _split_groups(real_groups)

    def _collect(groups, keys):
        files = []
        for k in keys:
            files.extend([r["file_id"] for r in groups[k]])
        return files

    train_ids = _collect(fake_groups, fake_train_keys) + _collect(real_groups, real_train_keys)
    val_ids   = _collect(fake_groups, fake_val_keys)   + _collect(real_groups, real_val_keys)
    test_ids  = _collect(fake_groups, fake_test_keys)  + _collect(real_groups, real_test_keys)

    # Sanity: no overlap
    train_set = set(train_ids)
    val_set   = set(val_ids)
    test_set  = set(test_ids)
    assert len(train_set & val_set) == 0,   "LEAK: train/val overlap"
    assert len(train_set & test_set) == 0,  "LEAK: train/test overlap"
    assert len(val_set & test_set) == 0,    "LEAK: val/test overlap"

    # Speaker leakage check
    def _speakers_in(fids: set, all_records: list) -> set:
        fid_map = {r["file_id"]: r for r in all_records}
        return {fid_map[fid]["speaker_id"] for fid in fids
                if fid in fid_map and fid_map[fid]["speaker_id"] != "unknown"}

    train_spks = _speakers_in(train_set, records)
    test_spks  = _speakers_in(test_set, records)
    spk_overlap = train_spks & test_spks

    return {
        "split_name": "A_standard",
        "description": "70/15/15 group-aware split by speaker/source",
        "seed": seed,
        "train_ratio": TRAIN_RATIO,
        "val_ratio": VAL_RATIO,
        "test_ratio": TEST_RATIO,
        "train_ids": sorted(train_ids),
        "val_ids":   sorted(val_ids),
        "test_ids":  sorted(test_ids),
        "n_train": len(train_ids),
        "n_val":   len(val_ids),
        "n_test":  len(test_ids),
        "speaker_overlap_train_test": sorted(spk_overlap),
        "speaker_overlap_count": len(spk_overlap),
        "file_overlap_count": len(train_set & test_set),
        "leakage_check": "PASS" if len(spk_overlap) == 0 and len(train_set & test_set) == 0 else "FAIL",
    }


# ---------------------------------------------------------------------------
# Split B: Generator holdout
# ---------------------------------------------------------------------------

def split_B_generator_holdout(records: list[dict], seed: int,
                                holdout_generator: str = None) -> dict:
    """
    Hold one FAKE generator entirely out of training.

    Selection logic:
      - If holdout_generator is specified, use it.
      - Otherwise, select the generator with the most samples that is NOT 'unknown'
        or 'human_speech' — this maximises the diagnostic value of the holdout.

    REAL samples: use all REAL records in training (they are human speech, no generator).
    FAKE train: all FAKE except holdout generator.
    FAKE test:  only holdout generator.

    The remaining FAKE train samples get a standard 85/15 train/val split.
    """
    import random as _random
    rng = _random.Random(seed)

    fake_records = [r for r in records if r["label"] == "FAKE"]
    real_records = [r for r in records if r["label"] == "REAL"]

    # Count generators among FAKE records
    gen_counts = defaultdict(list)
    for r in fake_records:
        gid = r.get("generator_id", "unknown")
        if gid not in {"unknown", "human_speech"}:
            gen_counts[gid].append(r["file_id"])

    if not gen_counts:
        return {
            "split_name": "B_generator_holdout",
            "status": "SKIPPED",
            "reason": "No named generators found in FAKE records. All generators are 'unknown'.",
            "available_generators": [],
        }

    print(f"[Split B] Available FAKE generators: {dict({k: len(v) for k, v in gen_counts.items()})}")

    if holdout_generator and holdout_generator in gen_counts:
        selected_holdout = holdout_generator
    else:
        if holdout_generator:
            print(f"[Split B] Requested holdout '{holdout_generator}' not found. Auto-selecting.")
        # Pick the generator with the most samples (best statistical coverage in test)
        selected_holdout = max(gen_counts, key=lambda g: len(gen_counts[g]))

    holdout_ids = set(gen_counts[selected_holdout])
    remaining_fake = [r for r in fake_records if r["file_id"] not in holdout_ids]

    print(f"[Split B] Holdout generator: '{selected_holdout}' ({len(holdout_ids)} files)")
    print(f"[Split B] Training FAKE (non-holdout): {len(remaining_fake)} files")

    # Split remaining FAKE into train/val (85/15)
    fake_groups = build_groups(remaining_fake)
    fake_keys = sorted(fake_groups.keys())
    rng.shuffle(fake_keys)
    n_val = max(1, int(len(fake_keys) * 0.15))
    fake_val_keys = fake_keys[:n_val]
    fake_train_keys = fake_keys[n_val:]

    # Split REAL into train/val (85/15)
    real_groups = build_groups(real_records)
    real_keys = sorted(real_groups.keys())
    rng.shuffle(real_keys)
    n_real_val = max(1, int(len(real_keys) * 0.15))
    real_val_keys = real_keys[:n_real_val]
    real_train_keys = real_keys[n_real_val:]

    def _ids(groups, keys):
        return [r["file_id"] for k in keys for r in groups[k]]

    train_ids = _ids(fake_groups, fake_train_keys) + _ids(real_groups, real_train_keys)
    val_ids   = _ids(fake_groups, fake_val_keys)   + _ids(real_groups, real_val_keys)
    test_ids  = sorted(holdout_ids)

    train_set = set(train_ids)
    test_set  = set(test_ids)
    val_set   = set(val_ids)

    assert len(train_set & test_set) == 0, "LEAK: holdout test in train"
    assert len(val_set & test_set) == 0,   "LEAK: holdout test in val"

    return {
        "split_name": "B_generator_holdout",
        "description": f"Generator holdout: '{selected_holdout}' reserved for test only",
        "seed": seed,
        "holdout_generator": selected_holdout,
        "available_generators": sorted(gen_counts.keys()),
        "holdout_generator_test_count": len(holdout_ids),
        "train_ids": sorted(train_ids),
        "val_ids":   sorted(val_ids),
        "test_ids":  test_ids,
        "n_train": len(train_ids),
        "n_val":   len(val_ids),
        "n_test":  len(test_ids),
        "file_overlap_train_test": len(train_set & test_set),
        "leakage_check": "PASS" if len(train_set & test_set) == 0 else "FAIL",
        "status": "READY",
    }


# ---------------------------------------------------------------------------
# Validate splits
# ---------------------------------------------------------------------------

def validate_splits(split_A: dict, split_B: dict, records: list[dict]) -> dict:
    """Run all leakage checks and return a validation report."""
    report = {"split_A": {}, "split_B": {}}
    fid_to_record = {r["file_id"]: r for r in records}

    # ---- Split A ----
    if "train_ids" in split_A:
        train_ids = set(split_A["train_ids"])
        val_ids   = set(split_A["val_ids"])
        test_ids  = set(split_A["test_ids"])

        tv_overlap = train_ids & val_ids
        tt_overlap = train_ids & test_ids
        vt_overlap = val_ids & test_ids

        # Speaker overlap train/test
        def spks(id_set):
            return {fid_to_record[fid]["speaker_id"]
                    for fid in id_set
                    if fid in fid_to_record and fid_to_record[fid]["speaker_id"] != "unknown"}

        spk_tt_overlap = spks(train_ids) & spks(test_ids)

        # Label distribution
        def label_dist(id_set):
            counts = {"REAL": 0, "FAKE": 0}
            for fid in id_set:
                if fid in fid_to_record:
                    counts[fid_to_record[fid]["label"]] += 1
            return counts

        report["split_A"] = {
            "n_train": len(train_ids),
            "n_val": len(val_ids),
            "n_test": len(test_ids),
            "train_label_dist": label_dist(train_ids),
            "val_label_dist": label_dist(val_ids),
            "test_label_dist": label_dist(test_ids),
            "train_val_file_overlap": len(tv_overlap),
            "train_test_file_overlap": len(tt_overlap),
            "val_test_file_overlap": len(vt_overlap),
            "train_test_speaker_overlap": len(spk_tt_overlap),
            "file_leakage_check": "PASS" if len(tt_overlap) == 0 else "FAIL",
            "speaker_leakage_check": "PASS" if len(spk_tt_overlap) == 0 else "FAIL",
        }

    # ---- Split B ----
    if split_B.get("status") == "READY" and "train_ids" in split_B:
        train_ids = set(split_B["train_ids"])
        test_ids  = set(split_B["test_ids"])
        tt_overlap = train_ids & test_ids

        # Verify holdout generator not in train
        holdout = split_B.get("holdout_generator", "")
        holdout_in_train = [
            fid for fid in train_ids
            if fid in fid_to_record and fid_to_record[fid].get("generator_id") == holdout
        ]

        report["split_B"] = {
            "holdout_generator": holdout,
            "n_train": len(train_ids),
            "n_val": len(split_B.get("val_ids", [])),
            "n_test": len(test_ids),
            "train_test_file_overlap": len(tt_overlap),
            "holdout_generator_in_train": len(holdout_in_train),
            "file_leakage_check": "PASS" if len(tt_overlap) == 0 else "FAIL",
            "generator_leakage_check": "PASS" if len(holdout_in_train) == 0 else "FAIL",
        }
    else:
        report["split_B"] = {"status": split_B.get("status", "UNKNOWN"),
                              "reason": split_B.get("reason", "")}

    return report


# ---------------------------------------------------------------------------
# Duration / sample rate statistics
# ---------------------------------------------------------------------------

def dataset_statistics(records: list[dict]) -> dict:
    durations = [float(r["duration_seconds"]) for r in records
                 if r.get("duration_seconds") not in (None, "", "None")]
    sample_rates = [int(r["sample_rate"]) for r in records
                    if r.get("sample_rate") not in (None, "", "None")]
    generators = sorted(set(r["generator_id"] for r in records))
    speakers = sorted(set(r["speaker_id"] for r in records
                          if r["speaker_id"] != "unknown"))
    datasets_seen = sorted(set(r["dataset"] for r in records))

    stats = {
        "total": len(records),
        "n_real": sum(1 for r in records if r["label"] == "REAL"),
        "n_fake": sum(1 for r in records if r["label"] == "FAKE"),
        "datasets": datasets_seen,
        "generators": generators,
        "n_generators": len(generators),
        "n_speakers_known": len(speakers),
        "speakers_known": speakers[:50],  # cap for readability
    }

    if durations:
        import statistics as _stats
        stats["duration_min_s"] = round(min(durations), 2)
        stats["duration_max_s"] = round(max(durations), 2)
        stats["duration_mean_s"] = round(_stats.mean(durations), 2)
        stats["duration_median_s"] = round(_stats.median(durations), 2)
        stats["total_hours"] = round(sum(durations) / 3600, 2)

    if sample_rates:
        from collections import Counter
        sr_dist = dict(Counter(sample_rates).most_common())
        stats["sample_rate_distribution"] = sr_dist

    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ADIS Custom Detector — Manifest & Splits")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--holdout-generator", type=str, default=None,
                        help="Force a specific generator_id as holdout for Split B")
    args = parser.parse_args()

    # Load acquisition manifest
    acq_manifest = METADATA_DIR / "acquisition_manifest.csv"
    if not acq_manifest.is_file():
        print(f"[ERROR] Acquisition manifest not found: {acq_manifest}")
        print("        Run 01_acquire_data.py first.")
        sys.exit(1)

    print(f"[Manifest] Loading: {acq_manifest}")
    records = load_manifest(acq_manifest)
    print(f"[Manifest] Loaded {len(records)} records")

    if len(records) == 0:
        print("[ERROR] Manifest is empty. No data to work with.")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Step 1: Verify manifest
    # -----------------------------------------------------------------------
    print("\n[Manifest] Verifying...")
    ver = verify_manifest(records)
    print(f"  Total:         {ver['total_records']}")
    print(f"  REAL:          {ver['n_real']}")
    print(f"  FAKE:          {ver['n_fake']}")
    print(f"  Dup IDs:       {ver['duplicate_ids']}")
    print(f"  Missing paths: {ver['missing_paths']}")
    print(f"  Invalid labels:{ver['invalid_labels']}")
    if ver["issues"]:
        print(f"  Issues: {ver['issues'][:5]}")

    # Remove records with invalid labels
    clean_records = [r for r in records if r.get("label") in {"REAL", "FAKE"}]
    if len(clean_records) < len(records):
        print(f"[Manifest] Removed {len(records) - len(clean_records)} records with invalid labels")

    records = clean_records

    # -----------------------------------------------------------------------
    # Step 2: Dataset statistics
    # -----------------------------------------------------------------------
    print("\n[Stats] Computing dataset statistics...")
    stats = dataset_statistics(records)
    print(json.dumps(stats, indent=2))

    # -----------------------------------------------------------------------
    # Step 3: Save cleaned manifest
    # -----------------------------------------------------------------------
    clean_manifest_path = METADATA_DIR / "dataset_manifest.csv"
    save_manifest(records, clean_manifest_path)
    print(f"\n[Manifest] Saved cleaned manifest: {clean_manifest_path}")

    # -----------------------------------------------------------------------
    # Step 4: Build Split A
    # -----------------------------------------------------------------------
    print("\n[Split A] Building standard 70/15/15 split...")
    split_A = split_A_standard(records, args.seed)
    print(f"  Train: {split_A['n_train']}  Val: {split_A['n_val']}  Test: {split_A['n_test']}")
    print(f"  Speaker overlap train/test: {split_A['speaker_overlap_count']}")
    print(f"  File overlap train/test:    {split_A['file_overlap_count']}")
    print(f"  Leakage check: {split_A['leakage_check']}")

    # -----------------------------------------------------------------------
    # Step 5: Build Split B
    # -----------------------------------------------------------------------
    print("\n[Split B] Building generator holdout split...")
    split_B = split_B_generator_holdout(records, args.seed, args.holdout_generator)
    if split_B.get("status") == "SKIPPED":
        print(f"  SKIPPED: {split_B['reason']}")
    else:
        print(f"  Holdout generator:    {split_B['holdout_generator']}")
        print(f"  Train: {split_B['n_train']}  Val: {split_B['n_val']}  Test: {split_B['n_test']}")
        print(f"  Leakage check: {split_B['leakage_check']}")

    # -----------------------------------------------------------------------
    # Step 6: Validate splits
    # -----------------------------------------------------------------------
    print("\n[Validation] Running leakage checks...")
    validation = validate_splits(split_A, split_B, records)
    print(json.dumps(validation, indent=2))

    # -----------------------------------------------------------------------
    # Save all outputs
    # -----------------------------------------------------------------------
    split_A_path = METADATA_DIR / "split_A_standard.json"
    split_B_path = METADATA_DIR / "split_B_generator_holdout.json"
    summary_path = METADATA_DIR / "split_summary.json"
    stats_path   = METADATA_DIR / "dataset_statistics.json"

    with open(split_A_path, "w") as f:
        json.dump(split_A, f, indent=2)
    print(f"[Output] Split A saved: {split_A_path}")

    with open(split_B_path, "w") as f:
        json.dump(split_B, f, indent=2)
    print(f"[Output] Split B saved: {split_B_path}")

    split_summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "random_seed": args.seed,
        "total_records": len(records),
        "dataset_statistics": stats,
        "manifest_verification": ver,
        "split_validation": validation,
    }
    with open(summary_path, "w") as f:
        json.dump(split_summary, f, indent=2)
    print(f"[Output] Split summary saved: {summary_path}")

    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"[Output] Dataset statistics saved: {stats_path}")

    # -----------------------------------------------------------------------
    # Final leakage verdict
    # -----------------------------------------------------------------------
    print("\n" + "="*60)
    print("SPLIT LEAKAGE VALIDATION RESULTS")
    print("="*60)

    sa = validation.get("split_A", {})
    sb = validation.get("split_B", {})

    print(f"Split A — File leakage:    {sa.get('file_leakage_check', 'N/A')}")
    print(f"Split A — Speaker leakage: {sa.get('speaker_leakage_check', 'N/A')}")
    if sb.get("status") not in ("SKIPPED", "UNKNOWN", None):
        print(f"Split B — File leakage:    {sb.get('file_leakage_check', 'N/A')}")
        print(f"Split B — Gen leakage:     {sb.get('generator_leakage_check', 'N/A')}")
    else:
        print(f"Split B — Status:          {sb.get('status', 'N/A')}")

    all_pass = all([
        sa.get("file_leakage_check") == "PASS",
        sa.get("speaker_leakage_check") == "PASS",
    ])
    print(f"\nOverall leakage verdict: {'PASS' if all_pass else 'FAIL'}")
    print("="*60)


if __name__ == "__main__":
    main()
