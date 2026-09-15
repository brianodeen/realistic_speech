"""
Personal Voice Ingestion & Adaptation Tool for Vocalis Neural Architecture.
Prepares, cleans, and adapts personal voice recordings for custom voice modeling.
Designed for 100% offline local execution on NVIDIA RTX GPUs / CPU.
"""

import argparse
import glob
import os
import sys
import numpy as np
import soundfile as sf
from scipy import signal

TARGET_SAMPLE_RATE = 16000


def clean_and_normalize_audio(input_file: str, output_file: str, target_sr: int = TARGET_SAMPLE_RATE) -> dict:
    """
    Cleans, resamples, trims silence, and peak-normalizes a voice recording.
    """
    data, sr = sf.read(input_file, dtype="float32")
    if len(data.shape) > 1:
        data = data.mean(axis=1)  # Convert stereo to mono

    # Resample to target sample rate if necessary
    if sr != target_sr:
        num_target = int(len(data) * (target_sr / sr))
        data = signal.resample(data, num_target).astype(np.float32)

    # Trim leading and trailing silence
    abs_data = np.abs(data)
    threshold = 0.01
    active_indices = np.where(abs_data > threshold)[0]
    if len(active_indices) > 0:
        pad = int(0.08 * target_sr)  # 80ms pad
        start = max(0, active_indices[0] - pad)
        end = min(len(data), active_indices[-1] + pad)
        data = data[start:end]

    # Peak normalization to -1.0 dBFS
    peak = np.max(np.abs(data))
    if peak > 1e-4:
        data = (data / peak) * 0.89

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    sf.write(output_file, data, target_sr)

    duration = len(data) / target_sr
    rms = np.sqrt(np.mean(data**2))
    return {"file": output_file, "duration_sec": duration, "rms": float(rms), "samples": len(data)}


def prepare_dataset(input_dir: str, processed_dir: str) -> list:
    """
    Processes all audio clips found in input_dir and saves clean WAVs to processed_dir.
    """
    extensions = ["*.wav", "*.mp3", "*.flac", "*.m4a", "*.ogg"]
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(input_dir, ext)))
        files.extend(glob.glob(os.path.join(input_dir, ext.upper())))

    if not files:
        print(f"[VoiceCloner] No audio files found in '{input_dir}'.")
        print(f"[VoiceCloner] Place your recordings in '{input_dir}' and rerun.")
        return []

    print(f"[VoiceCloner] Found {len(files)} audio recordings in '{input_dir}'.")
    manifest = []
    total_duration = 0.0

    for idx, filepath in enumerate(sorted(files)):
        fname = f"sample_{idx:03d}.wav"
        out_path = os.path.join(processed_dir, fname)
        stats = clean_and_normalize_audio(filepath, out_path)
        stats["original_path"] = filepath
        manifest.append(stats)
        total_duration += stats["duration_sec"]
        print(f"  Processed [{idx+1}/{len(files)}]: {os.path.basename(filepath)} -> {stats['duration_sec']:.2f}s")

    print(f"\n[VoiceCloner] Processed dataset successfully:")
    print(f"  Total Clips: {len(manifest)}")
    print(f"  Total Clean Duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
    print(f"  Output Directory: {processed_dir}")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Vocalis Voice Cloner & Ingestion Pipeline")
    parser.add_argument("--prepare", action="store_true", help="Process raw recordings from input directory")
    parser.add_argument("--input-dir", "-i", type=str, default="data/my_voice_raw", help="Directory containing your voice recordings")
    parser.add_argument("--output-dir", "-o", type=str, default="data/my_voice_processed", help="Directory to store processed dataset")
    parser.add_argument("--status", action="store_true", help="Check dataset status")

    args = parser.parse_args()

    if args.prepare:
        prepare_dataset(args.input_dir, args.output_dir)
    elif args.status:
        processed_files = glob.glob(os.path.join(args.output_dir, "*.wav"))
        if not processed_files:
            print(f"[VoiceCloner] No processed files in '{args.output_dir}'.")
            print(f"  To prepare: place audio in '{args.input_dir}' and run:")
            print(f"  python tools/voice_cloner.py --prepare")
        else:
            total_dur = sum(len(sf.read(f)[0]) / TARGET_SAMPLE_RATE for f in processed_files)
            print(f"[VoiceCloner] Active Dataset: {len(processed_files)} clips, {total_dur:.1f}s total.")
    else:
        parser.print_help()
        print("\nQuick Start:")
        print(f"1. Save your microphone recordings (.wav or .mp3) into: {args.input_dir}/")
        print("2. Run: python tools/voice_cloner.py --prepare")
        print("3. Check: python tools/voice_cloner.py --status")


if __name__ == "__main__":
    main()
