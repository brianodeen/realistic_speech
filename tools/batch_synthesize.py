"""
Conlang Batch Speech Synthesizer.
Batch generates audio files for constructed language lexicons, phrasebooks,
and wordlists using the local offline VITS neural engine.
Supports CSV, JSON, YAML, and TXT input formats.
"""

import argparse
import csv
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import yaml
from pathlib import Path

from neural_synthesizer import NeuralSynthesizer


def load_items_from_csv(csv_path: str) -> list:
    items = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Flexible column header detection
            text = row.get("ipa") or row.get("text") or row.get("phrase") or row.get("word") or ""
            file_id = row.get("id") or row.get("filename") or row.get("key") or ""
            is_ipa = "ipa" in row or row.get("is_ipa", "").lower() in ["true", "1", "yes"]
            speed = float(row.get("speed", 1.2)) if row.get("speed") else 1.2
            if text:
                items.append({
                    "id": file_id or text.replace(" ", "_"),
                    "text": text,
                    "is_ipa": is_ipa,
                    "speed": speed,
                })
    return items


def load_items_from_json(json_path: str) -> list:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = []
    if isinstance(data, list):
        for idx, entry in enumerate(data):
            if isinstance(entry, str):
                items.append({"id": f"item_{idx:03d}", "text": entry, "is_ipa": False, "speed": 1.2})
            elif isinstance(entry, dict):
                text = entry.get("ipa") or entry.get("text") or entry.get("phrase") or entry.get("word") or ""
                file_id = entry.get("id") or entry.get("filename") or f"item_{idx:03d}"
                is_ipa = "ipa" in entry or entry.get("is_ipa", False)
                speed = float(entry.get("speed", 1.2))
                if text:
                    items.append({"id": file_id, "text": text, "is_ipa": is_ipa, "speed": speed})
    elif isinstance(data, dict):
        # Key-value dictionary (e.g. {"greeting": "mraow", "farewell": "purr"})
        for k, v in data.items():
            if isinstance(v, str):
                items.append({"id": k, "text": v, "is_ipa": False, "speed": 1.2})
            elif isinstance(v, dict):
                text = v.get("ipa") or v.get("text") or v.get("phrase") or ""
                items.append({"id": k, "text": text, "is_ipa": v.get("is_ipa", False), "speed": float(v.get("speed", 1.2))})
    return items


def load_items_from_txt(txt_path: str) -> list:
    items = []
    with open(txt_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Check for delimiter (tab or comma or pipe)
            if "\t" in line:
                parts = line.split("\t", 1)
                items.append({"id": parts[0].strip(), "text": parts[1].strip(), "is_ipa": False, "speed": 1.2})
            elif "|" in line:
                parts = line.split("|", 1)
                items.append({"id": parts[0].strip(), "text": parts[1].strip(), "is_ipa": False, "speed": 1.2})
            else:
                items.append({"id": f"phrase_{idx+1:03d}", "text": line, "is_ipa": False, "speed": 1.2})
    return items


def batch_synthesize(
    input_file: str,
    output_dir: str,
    force_ipa: bool = False,
    default_speed: float = 1.2,
    noise_scale: float = 0.667,
    noise_scale_duration: float = 0.8,
) -> dict:
    ext = os.path.splitext(input_file)[1].lower()
    if ext == ".csv":
        items = load_items_from_csv(input_file)
    elif ext == ".json":
        items = load_items_from_json(input_file)
    elif ext in [".yaml", ".yml"]:
        with open(input_file, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        # Convert to items
        items = []
        if isinstance(raw, list):
            for idx, entry in enumerate(raw):
                if isinstance(entry, str):
                    items.append({"id": f"item_{idx:03d}", "text": entry, "is_ipa": force_ipa, "speed": default_speed})
                elif isinstance(entry, dict):
                    t = entry.get("ipa") or entry.get("text") or entry.get("phrase") or ""
                    items.append({"id": entry.get("id", f"item_{idx:03d}"), "text": t, "is_ipa": force_ipa or "ipa" in entry, "speed": entry.get("speed", default_speed)})
        elif isinstance(raw, dict):
            for k, v in raw.items():
                if isinstance(v, str):
                    items.append({"id": k, "text": v, "is_ipa": force_ipa, "speed": default_speed})
                elif isinstance(v, dict):
                    t = v.get("ipa") or v.get("text") or v.get("phrase") or ""
                    items.append({"id": k, "text": t, "is_ipa": force_ipa or "ipa" in v, "speed": v.get("speed", default_speed)})
    else:
        items = load_items_from_txt(input_file)

    if not items:
        print(f"[BatchSynthesizer] No valid items parsed from '{input_file}'.")
        return {}

    os.makedirs(output_dir, exist_ok=True)
    synth = NeuralSynthesizer()

    manifest = {}
    print(f"\n[BatchSynthesizer] Synthesizing {len(items)} conlang phrases into '{output_dir}/'...")

    for idx, item in enumerate(items):
        file_id = item["id"]
        # sanitize filename
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in file_id)
        if not safe_name:
            safe_name = f"phrase_{idx:03d}"
        out_wav = os.path.join(output_dir, f"{safe_name}.wav")
        is_ipa = force_ipa or item.get("is_ipa", False)
        speed = float(item.get("speed") or default_speed)

        synth.synthesize_to_file(
            text=item["text"],
            output_path=out_wav,
            is_ipa=is_ipa,
            speaking_rate=speed,
            noise_scale=noise_scale,
            noise_scale_duration=noise_scale_duration,
        )

        manifest[file_id] = {
            "text": item["text"],
            "is_ipa": is_ipa,
            "speed": speed,
            "output_file": os.path.relpath(out_wav, output_dir),
        }
        print(f"  [{idx+1}/{len(items)}] '{item['text']}' -> {safe_name}.wav")

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[BatchSynthesizer] Completed {len(items)} audio files!")
    print(f"  Manifest written to: {manifest_path}\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Batch Conlang Speech Synthesizer")
    parser.add_argument("--lexicon", "-l", type=str, required=True, help="Path to lexicon file (.csv, .json, .yaml, or .txt)")
    parser.add_argument("--output-dir", "-o", type=str, default="output/conlang_audio", help="Directory to save generated .wav files")
    parser.add_argument("--ipa", action="store_true", help="Force treat all text entries as IPA phonetic strings")
    parser.add_argument("--speed", type=float, default=1.2, help="Default speaking rate / pace (default: 1.2)")
    parser.add_argument("--noise-scale", type=float, default=0.667, help="Pitch variation scale (default: 0.667)")

    args = parser.parse_args()
    batch_synthesize(
        input_file=args.lexicon,
        output_dir=args.output_dir,
        force_ipa=args.ipa,
        default_speed=args.speed,
        noise_scale=args.noise_scale,
    )


if __name__ == "__main__":
    main()
