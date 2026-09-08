"""
Inspect RVCBench dataset structure — check if audio data is embedded or just paths.
Also check VCTK config.
"""
import os
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
from datasets import load_dataset

def inspect_config(name, n=2):
    print(f"\n{'='*50}")
    print(f"Config: {name}")
    print('='*50)
    ds = load_dataset('Nanboy/RVCBench', name, split='default', streaming=True)
    for i, row in enumerate(ds):
        if i >= n:
            break
        print(f"Row {i} columns: {list(row.keys())}")
        audio_cols = [k for k in row.keys() if 'audio' in k.lower()]
        if audio_cols:
            print(f"  Audio columns: {audio_cols}")
        else:
            print("  NO audio columns found — dataset is metadata-only (file paths)")
        for k, v in row.items():
            if k in ('prompt_phonemes', 'prompt_tone', 'target_phonemes', 'target_tone',
                     'prompt_word2ph', 'target_word2ph'):
                continue
            print(f"  {k}: {repr(str(v))[:100]}")
        break  # just first row

for cfg in ['Libritts', 'VCTK']:
    inspect_config(cfg)
