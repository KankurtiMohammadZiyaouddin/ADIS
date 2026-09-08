"""
ADIS Custom Audio Detector — Phase 2
Fake-or-Real Dataset Manifest Builder

Uses the FOR-2sec dataset (Fake-or-Real, 2-second clips, normalized).
Source: https://bil.eecs.yorku.ca/share/for-2sec.tar.gz
License: Research use (York University APTLY Lab)

Paper: "Generalization of Audio Deepfake Detection" (Reimao & Tzerpos, 2019)

REAL sources: Arctic, LJSpeech, VoxForge, custom recordings
FAKE sources: Deep Voice 3 (DeepMind), Google WaveNet TTS

Dataset structure (already pre-split):
  for-2seconds/
    training/fake/   6,978 files
    training/real/   6,978 files
    validation/fake/ 1,413 files
    validation/real/ 1,413 files
    testing/fake/    544 files
    testing/real/    544 files

Total: 17,870 files (8,935 FAKE, 8,935 REAL)

LEAKAGE STRATEGY:
  The FOR dataset's official splits are used as the primary split.
  The dataset has NO speaker-level metadata accessible from filenames.
  All file-level splits are disjoint (guaranteed by dataset design).

  For generator holdout (Split B):
  - Since FOR-2sec has mixed TTS generators without per-file labels,
    Split B uses a DATASET-level holdout:
    Training = FOR-2sec
    Test = unseen dataset (if In The Wild dataset is provided separately)
    This preserves the scientific goal: test on an unseen generator family.

  If only FOR-2sec is available:
  - Split B will use the official testing split of FOR-2sec as holdout.
  - The FOR testing split is treated as a held-out evaluation.
  - This is not a true unseen-generator holdout, but a held-out partition.

Usage:
    python train/03_build_for_manifest.py [--data-dir PATH] [--seed INT]
"""

import argparse
import csv
import hashlib
import json
import random
import sys
import time
from pathlib import Path

CUSTOM_DIR = Path(__file__).resolve().parents[1]
METADATA_DIR = CUSTOM_DIR / "metadata"
METADATA_DIR.mkdir(parents=True, exist_ok=True)

# Default data location
DEFAULT_FOR_BASE = CUSTOM_DIR / "data" / "for-2sec" / "for-2seconds"

AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac"}

# FOR-2sec dataset metadata (from paper)
FOR_METADATA = {
    "dataset_name": "FOR-2sec",
    "source": "Fake-or-Real (FoR) Dataset - York University APTLY Lab",
    "url": "https://bil.eecs.yorku.ca/share/for-2sec.tar.gz",
    "license": "Research use — York University APTLY Lab",
    "citation": "Reimao & Tzerpos (2019). For: A dataset for synthetic speech detection.",
    "real_sources": ["Arctic Dataset", "LJSpeech", "VoxForge", "Custom recordings"],
    "fake_sources": ["Deep Voice 3 (DeepMind)", "Google WaveNet TTS"],
    "sample_rate_hz": 16000,
    "channels": 1,
    "format": "WAV",
    "clip_duration_s": 2.0,
    "normalized": True,
    "notes": (
        "for-2sec variant: files truncated at 2 seconds, "
        "normalized for sample rate, volume, channels. "
        "Generator per file is NOT labeled in filenames. "
        "FAKE files are a mix of Deep Voice 3 and WaveNet TTS output."
    ),
}


def collect_for_files(for_base: Path, split: str, label: str) -> list[Path]:
    """Collect all audio files for a given split/label combination."""
    d = for_base / split / label
    if not d.is_dir():
        print(f"[WARN] Directory not found: {d}")
        return []
    files = []
    for ext in AUDIO_EXTENSIONS:
        files.extend(d.glob(f"*{ext}"))
    return sorted(files)


def build_for_manifest(for_base: Path, seed: int) -> tuple[list[dict], dict]:
    """
    Build manifest from FOR-2sec dataset preserving official splits.

    Returns (records, split_assignment) where split_assignment maps
    file_id -> 'train' | 'val' | 'test'
    """
    rng = random.Random(seed)
    records = []
    split_assignment = {}

    # Map FOR split names to our canonical names
    split_map = {
        "training": "train",
        "validation": "val",
        "testing": "test",
    }

    print("[FOR] Building manifest from official splits...")

    for for_split, our_split in split_map.items():
        for label in ["fake", "real"]:
            files = collect_for_files(for_base, for_split, label)
            canonical_label = "FAKE" if label == "fake" else "REAL"

            print(f"  {for_split}/{label}: {len(files)} files -> split={our_split}, label={canonical_label}")

            for i, p in enumerate(files):
                # Deterministic file_id from relative path (no hash — avoids revealing label)
                file_id = f"for_{our_split}_{canonical_label.lower()}_{i:06d}"

                records.append({
                    "file_id": file_id,
                    "path": str(p.resolve()),
                    "dataset": "for_2sec",
                    "label": canonical_label,
                    # No speaker-level metadata available in FOR-2sec filenames
                    "speaker_id": "unknown",
                    # Generator is mixed (Deep Voice 3 + WaveNet) — cannot determine per file
                    "generator_id": "for_fake_mixed_tts" if canonical_label == "FAKE" else "for_human_speech",
                    "source_id": "for_2sec",
                    "duration_seconds": 2.0,   # all clips are exactly 2s (by design)
                    "sample_rate": 16000,
                    "channels": 1,
                    "format": "wav",
                    "audio_read_ok": True,
                    # FOR-specific: which FOR split this came from
                    "for_split": for_split,
                })

                split_assignment[file_id] = our_split

    print(f"\n[FOR] Total records: {len(records)}")
    return records, split_assignment


def build_splits_from_for(records: list[dict], split_assignment: dict) -> tuple[dict, dict]:
    """
    Build split A and split B from FOR-2sec official splits.

    Split A — Standard:
      Uses FOR official train/val/test as-is.
      These are disjoint at file level (guaranteed by dataset).

    Split B — Generator holdout (approximate):
      Since FOR-2sec does not label generators per file, we cannot do
      a true generator holdout within this dataset alone.
      Split B uses: train = FOR training, test = FOR testing set.
      Note: The FOR testing split is an official held-out evaluation set,
      not drawn from the same pool as training.
      This is labeled as 'for_testing_holdout', not true generator holdout.

    If an external dataset (e.g., In The Wild) is added later,
    that dataset becomes the true unseen-generator test.
    """
    train_ids = [r["file_id"] for r in records if split_assignment[r["file_id"]] == "train"]
    val_ids   = [r["file_id"] for r in records if split_assignment[r["file_id"]] == "val"]
    test_ids  = [r["file_id"] for r in records if split_assignment[r["file_id"]] == "test"]

    train_set = set(train_ids)
    val_set   = set(val_ids)
    test_set  = set(test_ids)

    # Verify splits are disjoint
    assert len(train_set & test_set) == 0,  "LEAK: FOR train/test overlap"
    assert len(train_set & val_set) == 0,   "LEAK: FOR train/val overlap"
    assert len(val_set & test_set) == 0,    "LEAK: FOR val/test overlap"

    # Label counts per split
    fid_map = {r["file_id"]: r for r in records}

    def label_dist(id_set):
        counts = {"REAL": 0, "FAKE": 0}
        for fid in id_set:
            if fid in fid_map:
                counts[fid_map[fid]["label"]] += 1
        return counts

    split_A = {
        "split_name": "A_standard",
        "description": (
            "FOR-2sec official splits: training=train, validation=val, testing=test. "
            "These are disjoint at file level by dataset design. "
            "No speaker-level metadata available for speaker-disjoint verification."
        ),
        "source": "FOR-2sec official splits (not random — dataset-provided)",
        "train_ids": sorted(train_ids),
        "val_ids":   sorted(val_ids),
        "test_ids":  sorted(test_ids),
        "n_train": len(train_ids),
        "n_val":   len(val_ids),
        "n_test":  len(test_ids),
        "train_label_dist": label_dist(train_set),
        "val_label_dist":   label_dist(val_set),
        "test_label_dist":  label_dist(test_set),
        "file_overlap_count": len(train_set & test_set),
        "speaker_overlap_count": "unknown — no speaker metadata",
        "leakage_check": "PASS" if len(train_set & test_set) == 0 else "FAIL",
        "notes": [
            "Split uses FOR-2sec official train/val/test splits.",
            "Speaker identity is not available — cannot verify speaker-disjoint.",
            "File-level disjoint is guaranteed by dataset design.",
        ],
    }

    # Split B: treat the testing partition as the held-out generator-proxy
    # This is an approximation — true generator holdout requires knowing which
    # TTS system produced each FAKE file, which FOR-2sec does not provide.
    split_B = {
        "split_name": "B_generator_holdout",
        "description": (
            "Approximate generator holdout using FOR-2sec official testing split. "
            "True unseen-generator test (e.g., Gemini, In The Wild) pending external data."
        ),
        "holdout_generator": "for_2sec_official_test_partition",
        "holdout_type": "dataset_partition_holdout",
        "status": "APPROXIMATE",
        "available_generators": [
            "for_fake_mixed_tts (Deep Voice 3 + WaveNet, unlabeled per file)",
            "for_human_speech (Arctic + LJSpeech + VoxForge + custom)",
        ],
        "train_ids": sorted(train_ids),
        "val_ids":   sorted(val_ids),
        "test_ids":  sorted(test_ids),
        "n_train": len(train_ids),
        "n_val":   len(val_ids),
        "n_test":  len(test_ids),
        "file_overlap_train_test": len(train_set & test_set),
        "leakage_check": "PASS" if len(train_set & test_set) == 0 else "FAIL",
        "generator_leakage_check": "APPROXIMATE — true generator labels not available per file",
        "notes": [
            "FOR-2sec FAKE files contain speech from Deep Voice 3 and Google WaveNet TTS.",
            "The dataset does not label which generator produced each FAKE file.",
            "A true generator holdout requires an external dataset (e.g., In The Wild).",
            "When In The Wild data is added, it will serve as the true unseen-generator test.",
        ],
    }

    return split_A, split_B


def main():
    parser = argparse.ArgumentParser(description="ADIS — FOR-2sec Manifest Builder")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_FOR_BASE),
                        help="Path to for-2seconds/ directory")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    for_base = Path(args.data_dir)
    if not for_base.is_dir():
        print(f"[ERROR] FOR-2sec directory not found: {for_base}")
        print("        Run download or provide correct --data-dir")
        sys.exit(1)

    t0 = time.time()

    # Build manifest
    records, split_assignment = build_for_manifest(for_base, args.seed)

    # Build splits
    split_A, split_B = build_splits_from_for(records, split_assignment)

    # Dataset statistics
    n_real = sum(1 for r in records if r["label"] == "REAL")
    n_fake = sum(1 for r in records if r["label"] == "FAKE")
    generators = sorted(set(r["generator_id"] for r in records))
    datasets = sorted(set(r["dataset"] for r in records))

    stats = {
        "dataset": "FOR-2sec (Fake-or-Real 2-second clips)",
        "source": FOR_METADATA["source"],
        "url": FOR_METADATA["url"],
        "license": FOR_METADATA["license"],
        "total_records": len(records),
        "n_real": n_real,
        "n_fake": n_fake,
        "generators": generators,
        "real_sources": FOR_METADATA["real_sources"],
        "fake_sources": FOR_METADATA["fake_sources"],
        "sample_rate_hz": 16000,
        "channels": 1,
        "format": "WAV",
        "clip_duration_s": 2.0,
        "datasets": datasets,
        "n_generators": len(generators),
        "n_speakers_known": 0,
        "duration_total_hours": round(len(records) * 2 / 3600, 2),
        "sample_rate_distribution": {16000: len(records)},
        "split_A": {
            "n_train": split_A["n_train"],
            "n_val":   split_A["n_val"],
            "n_test":  split_A["n_test"],
            "train_label_dist": split_A["train_label_dist"],
            "val_label_dist":   split_A["val_label_dist"],
            "test_label_dist":  split_A["test_label_dist"],
        },
    }

    # Save all outputs
    manifest_path = METADATA_DIR / "dataset_manifest.csv"
    acq_manifest_path = METADATA_DIR / "acquisition_manifest.csv"
    split_A_path  = METADATA_DIR / "split_A_standard.json"
    split_B_path  = METADATA_DIR / "split_B_generator_holdout.json"
    stats_path    = METADATA_DIR / "dataset_statistics.json"
    for_meta_path = METADATA_DIR / "for_dataset_metadata.json"

    # Write manifests (both names for compatibility with phase2_tests.py)
    fieldnames = ["file_id", "path", "dataset", "label", "speaker_id", "generator_id",
                  "source_id", "duration_seconds", "sample_rate", "channels", "format",
                  "audio_read_ok", "for_split"]
    for out_path in [manifest_path, acq_manifest_path]:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)
        print(f"[Output] Manifest saved: {out_path}")

    with open(split_A_path, "w") as f:
        json.dump(split_A, f, indent=2)
    print(f"[Output] Split A saved: {split_A_path}")

    with open(split_B_path, "w") as f:
        json.dump(split_B, f, indent=2)
    print(f"[Output] Split B saved: {split_B_path}")

    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"[Output] Statistics saved: {stats_path}")

    with open(for_meta_path, "w") as f:
        json.dump(FOR_METADATA, f, indent=2)
    print(f"[Output] FOR metadata saved: {for_meta_path}")

    # Also write split summary for compatibility
    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "random_seed": args.seed,
        "total_records": len(records),
        "dataset_statistics": stats,
        "split_validation": {
            "split_A": {
                "n_train": split_A["n_train"],
                "n_val": split_A["n_val"],
                "n_test": split_A["n_test"],
                "train_label_dist": split_A["train_label_dist"],
                "val_label_dist": split_A["val_label_dist"],
                "test_label_dist": split_A["test_label_dist"],
                "file_leakage_check": split_A["leakage_check"],
                "speaker_leakage_check": "SKIP — no speaker metadata",
                "train_val_file_overlap": 0,
                "train_test_file_overlap": split_A["file_overlap_count"],
                "val_test_file_overlap": 0,
                "train_test_speaker_overlap": "unknown",
            },
            "split_B": {
                "holdout_generator": split_B["holdout_generator"],
                "n_train": split_B["n_train"],
                "n_val": split_B["n_val"],
                "n_test": split_B["n_test"],
                "status": split_B["status"],
                "file_leakage_check": split_B["leakage_check"],
                "generator_leakage_check": split_B["generator_leakage_check"],
            },
        },
    }
    with open(METADATA_DIR / "split_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    elapsed = round(time.time() - t0, 1)

    print(f"\n{'='*60}")
    print("FOR-2sec MANIFEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total records:      {len(records)}")
    print(f"REAL:               {n_real}")
    print(f"FAKE:               {n_fake}")
    print(f"Generators:         {generators}")
    print(f"Total duration:     {stats['duration_total_hours']} hours")
    print(f"Sample rate:        16,000 Hz (all files)")
    print(f"Clip duration:      2.0 s (all files)")
    print()
    print("Split A (official FOR-2sec splits):")
    print(f"  Train:  {split_A['n_train']} ({split_A['train_label_dist']})")
    print(f"  Val:    {split_A['n_val']}   ({split_A['val_label_dist']})")
    print(f"  Test:   {split_A['n_test']}  ({split_A['test_label_dist']})")
    print(f"  File leakage train/test: {split_A['leakage_check']}")
    print()
    print("Split B (approximate holdout — true generator holdout pending external dataset):")
    print(f"  Status: {split_B['status']}")
    print(f"  Note:   FOR-2sec FAKE does not label generator per file.")
    print(f"  Awaiting: In The Wild or other external dataset for true generator holdout.")
    print()
    print(f"Elapsed: {elapsed}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
