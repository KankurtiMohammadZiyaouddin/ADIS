"""
ADIS Custom Audio Detector — Phase 2
Step 1: Dataset Acquisition

Downloads a representative subset of:
  A) In The Wild Audio Deepfake  (Kaggle — CC BY 4.0)
  B) RVCBench                   (HuggingFace — CC0 1.0)

TARGET:
  REAL: 2,000–3,000 files
  FAKE: 2,000–3,000 files (from multiple generators)

LEAKAGE POLICY:
  - No audio file from training will appear in test.
  - Speaker splits are group-aware where IDs are available.
  - At least one generator is held out for generator-holdout evaluation.
  - Gemini sample is NEVER included here.

Usage:
    python train/01_acquire_data.py [--itw-path PATH] [--skip-rvcbench] [--skip-itw]

Arguments:
    --itw-path PATH   Path to locally extracted In The Wild dataset root.
                      If not given, script prints download instructions.
    --skip-rvcbench   Skip RVCBench download.
    --skip-itw        Skip In The Wild acquisition (if not available).
    --max-itw INT     Max files to sample from In The Wild per class (default: 2000).
    --max-rvc INT     Max generated files to sample from RVCBench (default: 1000).
    --seed INT        Random seed (default: 42).
"""

import argparse
import hashlib
import json
import os
import random
import shutil
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[4]
CUSTOM_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CUSTOM_DIR / "data"
ITW_FAKE_DIR = DATA_DIR / "in_the_wild" / "fake"
ITW_REAL_DIR = DATA_DIR / "in_the_wild" / "real"
RVCBENCH_DIR = DATA_DIR / "rvcbench"
METADATA_DIR = CUSTOM_DIR / "metadata"
METADATA_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".webm"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256_of_file(path: Path, max_bytes: int = 65536) -> str:
    """Compute SHA-256 of the first max_bytes of a file for fast dedup check."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read(max_bytes))
    return h.hexdigest()


def get_audio_info(path: Path) -> dict:
    """Read duration, sample rate, channels from an audio file."""
    try:
        import soundfile as sf
        info = sf.info(str(path))
        return {
            "duration_seconds": round(info.duration, 3),
            "sample_rate": info.samplerate,
            "channels": info.channels,
            "format": info.format.lower() if info.format else path.suffix.lstrip("."),
            "audio_read_ok": True,
        }
    except Exception as e:
        return {
            "duration_seconds": None,
            "sample_rate": None,
            "channels": None,
            "format": path.suffix.lstrip("."),
            "audio_read_ok": False,
            "audio_read_error": str(e),
        }


def collect_audio_files(directory: Path) -> list:
    """Recursively collect all audio files under directory."""
    files = []
    for p in directory.rglob("*"):
        if p.suffix.lower() in AUDIO_EXTENSIONS and p.is_file():
            files.append(p)
    return sorted(files)


# ---------------------------------------------------------------------------
# In The Wild acquisition
# ---------------------------------------------------------------------------

def acquire_itw(itw_root: Path, max_per_class: int, seed: int) -> list[dict]:
    """
    Collect a balanced sample from In The Wild dataset.

    Expected structure:
        <itw_root>/fake/*.wav
        <itw_root>/real/*.wav

    Returns list of record dicts.
    """
    rng = random.Random(seed)

    fake_dir = itw_root / "fake"
    real_dir = itw_root / "real"

    if not fake_dir.is_dir():
        # Try alternate structure: release_in_the_wild/fake
        alt = itw_root / "release_in_the_wild"
        if (alt / "fake").is_dir():
            fake_dir = alt / "fake"
            real_dir = alt / "real"
        else:
            print(f"[ERROR] Cannot find fake/ under {itw_root}")
            print("        Expected: <root>/fake/ or <root>/release_in_the_wild/fake/")
            return []

    fake_files = collect_audio_files(fake_dir)
    real_files = collect_audio_files(real_dir)

    print(f"[ITW] Found {len(fake_files)} FAKE files, {len(real_files)} REAL files")

    # Sample if larger than target
    if len(fake_files) > max_per_class:
        fake_files = rng.sample(fake_files, max_per_class)
        print(f"[ITW] Sampled {max_per_class} FAKE files (diversity-first)")
    if len(real_files) > max_per_class:
        real_files = rng.sample(real_files, max_per_class)
        print(f"[ITW] Sampled {max_per_class} REAL files")

    records = []

    def make_record(path: Path, label: str, idx: int) -> dict:
        info = get_audio_info(path)
        return {
            "file_id": f"itw_{label}_{idx:06d}",
            "path": str(path.resolve()),
            "dataset": "in_the_wild",
            "label": label,
            # ITW has no per-file speaker metadata — folder name is the only signal
            # We cannot infer speaker from filename without the metadata CSV
            # Mark as unknown to avoid leakage from invented IDs
            "speaker_id": "unknown",
            # ITW FAKE contains speech from multiple TTS systems, not separated by folder
            # Generator is unknown at the file level — no metadata CSV shipped with dataset
            "generator_id": "itw_mixed_tts" if label == "FAKE" else "human_speech",
            "source_id": "in_the_wild",
            **info,
        }

    print("[ITW] Reading audio metadata... (this may take a minute)")
    for i, p in enumerate(fake_files):
        if i % 200 == 0:
            print(f"  FAKE: {i}/{len(fake_files)}")
        records.append(make_record(p, "FAKE", i))

    for i, p in enumerate(real_files):
        if i % 200 == 0:
            print(f"  REAL: {i}/{len(real_files)}")
        records.append(make_record(p, "REAL", i))

    print(f"[ITW] Acquired {len(records)} records total")
    return records


# ---------------------------------------------------------------------------
# RVCBench acquisition via HuggingFace datasets
# ---------------------------------------------------------------------------

def acquire_rvcbench(output_dir: Path, max_generated: int, seed: int) -> list[dict]:
    """
    Download a representative RVCBench subset from HuggingFace.

    RVCBench structure:
      REAL  = reference/prompt audio (human recordings from LibriTTS, VCTK, etc.)
      FAKE  = generated audio from TTS/VC systems

    We use the 'LibriTTS' config as primary source because:
      - English, multi-speaker
      - 40 speakers, gender-balanced
      - Multiple modern TTS/VC generators
      - Well-documented

    For FAKE diversity, we sample from multiple generators if available.
    Returns list of record dicts.
    """
    try:
        from datasets import load_dataset, get_dataset_config_names
    except ImportError:
        print("[ERROR] 'datasets' package not found.")
        print("        Install with: pip install datasets")
        print("        Skipping RVCBench acquisition.")
        return []

    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("[RVCBench] Checking available configs...")
    try:
        configs = get_dataset_config_names("Nanboy/RVCBench")
        print(f"[RVCBench] Available configs: {configs}")
    except Exception as e:
        print(f"[RVCBench] Could not list configs: {e}")
        configs = ["Libritts"]  # fallback to known config

    # Priority configs: start with English multi-speaker for best speaker diversity
    priority_configs = [c for c in configs if c.lower() in {"libritts", "vctk", "multispeaker_libri"}]
    if not priority_configs:
        priority_configs = configs[:2] if configs else ["Libritts"]

    print(f"[RVCBench] Using configs: {priority_configs}")

    records = []
    seen_hashes = set()  # for exact-duplicate detection

    for config_name in priority_configs:
        print(f"\n[RVCBench] Loading config '{config_name}'...")
        try:
            ds = load_dataset("Nanboy/RVCBench", config_name, split="train", streaming=False)
        except Exception as e:
            print(f"[RVCBench] Could not load '{config_name}': {e}")
            try:
                # Try streaming mode
                ds = load_dataset("Nanboy/RVCBench", config_name, streaming=True)
            except Exception as e2:
                print(f"[RVCBench] Streaming also failed for '{config_name}': {e2}")
                continue

        print(f"[RVCBench] Dataset info: {ds}")

        # Inspect columns to understand structure
        try:
            sample = next(iter(ds)) if hasattr(ds, '__iter__') else ds[0]
            print(f"[RVCBench] Sample columns: {list(sample.keys())}")
        except Exception as e:
            print(f"[RVCBench] Could not peek sample: {e}")
            sample = {}

        col_keys = list(sample.keys()) if sample else []
        has_audio_col = any("audio" in k.lower() for k in col_keys)
        has_speaker_col = any("speaker" in k.lower() for k in col_keys)
        has_model_col = any(k.lower() in {"model", "vc_model", "tts_model", "generator", "system"} for k in col_keys)

        print(f"[RVCBench] has_audio_col={has_audio_col}, has_speaker={has_speaker_col}, has_model={has_model_col}")
        print(f"[RVCBench] All columns: {col_keys}")

        # Count and sample
        items = list(ds) if not hasattr(ds, 'num_rows') else ds
        try:
            total = len(items)
        except TypeError:
            items = list(ds)
            total = len(items)

        print(f"[RVCBench] {total} rows in config '{config_name}'")

        if total == 0:
            continue

        # Sample to keep manageable
        per_config_max = max_generated // len(priority_configs)
        if total > per_config_max:
            sampled_items = rng.sample(list(items) if not isinstance(items, list) else items, per_config_max)
        else:
            sampled_items = list(items) if not isinstance(items, list) else items

        print(f"[RVCBench] Processing {len(sampled_items)} rows from '{config_name}'...")

        for idx, row in enumerate(sampled_items):
            if idx % 100 == 0:
                print(f"  {idx}/{len(sampled_items)}")

            # Extract audio for each audio column (prompt = REAL, generated = FAKE)
            for col_name, row_label in _audio_columns_with_labels(col_keys):
                if col_name not in row:
                    continue

                audio_data = row[col_name]
                if audio_data is None:
                    continue

                # Extract array and sr
                try:
                    arr = audio_data.get("array") if isinstance(audio_data, dict) else None
                    sr = audio_data.get("sampling_rate", 16000) if isinstance(audio_data, dict) else 16000
                except Exception:
                    continue

                if arr is None:
                    continue

                # Dedup via quick hash of first 4k floats
                dedup_key = hashlib.md5(str(arr[:400] if len(arr) > 400 else arr).encode()).hexdigest()
                if dedup_key in seen_hashes:
                    continue
                seen_hashes.add(dedup_key)

                # Save to disk
                import numpy as np
                import soundfile as sf

                arr_np = np.array(arr, dtype=np.float32)
                duration = round(len(arr_np) / sr, 3)

                # Skip very short clips (< 0.5 s)
                if duration < 0.5:
                    continue

                filename = f"rvcbench_{config_name}_{col_name}_{idx:06d}.wav"
                out_path = output_dir / filename

                try:
                    sf.write(str(out_path), arr_np, sr)
                except Exception as e:
                    print(f"  [WARN] Could not write {filename}: {e}")
                    continue

                # Speaker ID
                speaker_id = "unknown"
                for sk in ["speaker_id", "speaker", "spk_id"]:
                    if sk in row and row[sk] is not None:
                        speaker_id = f"rvc_{str(row[sk])}"
                        break

                # Generator ID
                generator_id = "unknown"
                if row_label == "FAKE":
                    for gk in ["model", "vc_model", "tts_model", "generator", "system"]:
                        if gk in row and row[gk] is not None:
                            generator_id = f"rvc_{str(row[gk])}"
                            break
                    if generator_id == "unknown":
                        generator_id = f"rvc_{config_name}_generated"
                else:
                    generator_id = "human_speech"

                records.append({
                    "file_id": f"rvc_{config_name}_{col_name}_{idx:06d}",
                    "path": str(out_path.resolve()),
                    "dataset": f"rvcbench_{config_name}",
                    "label": row_label,
                    "speaker_id": speaker_id,
                    "generator_id": generator_id,
                    "source_id": f"rvcbench_{config_name}",
                    "duration_seconds": duration,
                    "sample_rate": sr,
                    "channels": 1,
                    "format": "wav",
                    "audio_read_ok": True,
                })

    print(f"\n[RVCBench] Acquired {len(records)} records total")
    return records


def _audio_columns_with_labels(col_keys: list) -> list[tuple]:
    """
    Map RVCBench column names to REAL/FAKE labels.

    RVCBench conventions (from documentation):
      prompt_audio / ori  = original human recording → REAL
      target_audio / gt   = generated/cloned speech  → FAKE
    """
    mappings = []
    for k in col_keys:
        kl = k.lower()
        if any(x in kl for x in ["prompt", "ori", "reference", "source_audio"]):
            mappings.append((k, "REAL"))
        elif any(x in kl for x in ["target", "gt", "generated", "cloned", "fake"]):
            mappings.append((k, "FAKE"))
    # If no clear mapping, skip — do not guess
    return mappings


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def deduplicate_records(records: list[dict]) -> tuple[list[dict], int]:
    """Remove exact duplicates by file_id. Report count removed."""
    seen_ids = set()
    deduped = []
    removed = 0
    for r in records:
        fid = r["file_id"]
        if fid in seen_ids:
            removed += 1
            continue
        seen_ids.add(fid)
        deduped.append(r)
    return deduped, removed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ADIS Custom Detector — Dataset Acquisition")
    parser.add_argument("--itw-path", type=str, default=None,
                        help="Path to In The Wild dataset root directory")
    parser.add_argument("--skip-rvcbench", action="store_true", default=False)
    parser.add_argument("--skip-itw", action="store_true", default=False)
    parser.add_argument("--max-itw", type=int, default=2000,
                        help="Max files per class from In The Wild")
    parser.add_argument("--max-rvc", type=int, default=1000,
                        help="Max total generated files from RVCBench")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    all_records = []
    t0 = time.time()

    # -----------------------------------------------------------------------
    # A) In The Wild
    # -----------------------------------------------------------------------
    if not args.skip_itw:
        if args.itw_path:
            itw_root = Path(args.itw_path)
            if not itw_root.is_dir():
                print(f"[ERROR] ITW path does not exist: {itw_root}")
                print("[INFO] Skipping In The Wild.")
            else:
                print(f"\n{'='*60}")
                print("DATASET A — In The Wild")
                print(f"{'='*60}")
                itw_records = acquire_itw(itw_root, args.max_itw, args.seed)
                all_records.extend(itw_records)
        else:
            print("\n[In The Wild] No --itw-path provided.")
            print("  To download In The Wild dataset:")
            print("  1. Go to: https://www.kaggle.com/datasets/abdallamohamed312/in-the-wild-audio-deepfake")
            print("  2. Download and extract to a local directory.")
            print("  3. Re-run with: --itw-path /path/to/extracted/root")
            print("  Expected structure: <root>/fake/*.wav + <root>/real/*.wav")
            print("  (or <root>/release_in_the_wild/fake/ etc.)")
            print("  [SKIPPING ITW for now — no path given]")

    # -----------------------------------------------------------------------
    # B) RVCBench
    # -----------------------------------------------------------------------
    if not args.skip_rvcbench:
        print(f"\n{'='*60}")
        print("DATASET B — RVCBench")
        print(f"{'='*60}")
        rvc_records = acquire_rvcbench(RVCBENCH_DIR, args.max_rvc, args.seed)
        all_records.extend(rvc_records)

    # -----------------------------------------------------------------------
    # Deduplicate
    # -----------------------------------------------------------------------
    all_records, n_removed = deduplicate_records(all_records)
    if n_removed > 0:
        print(f"\n[DEDUP] Removed {n_removed} duplicate file_ids.")

    if not all_records:
        print("\n[WARNING] No records collected. Check dataset paths and availability.")
        print("          Build manifest with 0 records — acquisition incomplete.")

    # -----------------------------------------------------------------------
    # Save raw acquisition manifest
    # -----------------------------------------------------------------------
    import csv

    out_path = METADATA_DIR / "acquisition_manifest.csv"
    fieldnames = [
        "file_id", "path", "dataset", "label", "speaker_id", "generator_id",
        "source_id", "duration_seconds", "sample_rate", "channels", "format",
        "audio_read_ok",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_records)

    elapsed = round(time.time() - t0, 1)

    # Summary
    labels = [r["label"] for r in all_records]
    n_real = labels.count("REAL")
    n_fake = labels.count("FAKE")
    datasets = sorted(set(r["dataset"] for r in all_records))
    generators = sorted(set(r["generator_id"] for r in all_records))
    speakers = sorted(set(r["speaker_id"] for r in all_records if r["speaker_id"] != "unknown"))
    failed = [r for r in all_records if not r.get("audio_read_ok", True)]

    print(f"\n{'='*60}")
    print("ACQUISITION SUMMARY")
    print(f"{'='*60}")
    print(f"Total records:     {len(all_records)}")
    print(f"REAL:              {n_real}")
    print(f"FAKE:              {n_fake}")
    print(f"Datasets:          {datasets}")
    print(f"Generators (known):{generators}")
    print(f"Speakers (known):  {len(speakers)}")
    print(f"Failed audio reads:{len(failed)}")
    print(f"Elapsed:           {elapsed}s")
    print(f"Manifest saved to: {out_path}")

    # Save acquisition summary JSON
    summary = {
        "acquisition_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_records": len(all_records),
        "n_real": n_real,
        "n_fake": n_fake,
        "datasets": datasets,
        "generators": generators,
        "known_speakers": len(speakers),
        "failed_audio_reads": len(failed),
        "random_seed": args.seed,
        "max_itw_per_class": args.max_itw,
        "max_rvc": args.max_rvc,
        "elapsed_seconds": elapsed,
    }
    summary_path = METADATA_DIR / "acquisition_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to:  {summary_path}")


if __name__ == "__main__":
    main()
