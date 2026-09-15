"""
Universal Neural Speech Synthesizer (VITS Local Architecture).
Synthesizes ultra-realistic, natural speech 100% locally on GPU/CPU with zero cloud dependencies.
Supports standard orthographic text, raw ExtIPA phonemes, and constructed language utterances.
"""

import argparse
import os
import sys
import numpy as np
import soundfile as sf
import torch

try:
    from transformers import VitsModel, AutoTokenizer
except ImportError:
    print("Error: transformers package is required. Please ensure transformers and torch are installed.")
    sys.exit(1)

from conlang_phonetics import prepare_conlang_utterance


class NeuralSynthesizer:
    def __init__(self, model_id: str = "facebook/mms-tts-eng", device: str = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"[NeuralSynthesizer] Loading model '{model_id}' on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = VitsModel.from_pretrained(model_id).to(self.device)
        self.sample_rate = self.model.config.sampling_rate
        print(f"[NeuralSynthesizer] Model ready. Sample rate: {self.sample_rate} Hz.")

    def synthesize(
        self,
        text: str,
        is_ipa: bool = False,
        speaking_rate: float = 1.2,
        noise_scale: float = 0.667,
        noise_scale_duration: float = 0.8,
    ) -> np.ndarray:
        """
        Synthesizes speech from text or IPA using local VITS stochastic forward pass.
        """
        # 1. Normalize phonetics for conlangs and IPA symbols
        norm_text = prepare_conlang_utterance(text, is_ipa=is_ipa)
        if not norm_text:
            return np.zeros(0, dtype=np.float32)

        # 2. Tokenize
        inputs = self.tokenizer(norm_text, return_tensors="pt").to(self.device)

        # 3. Configure stochastic and pacing hyperparameters
        self.model.speaking_rate = float(speaking_rate)
        self.model.noise_scale = float(noise_scale)
        self.model.noise_scale_duration = float(noise_scale_duration)

        # 4. Neural Forward Pass
        with torch.no_grad():
            output = self.model(**inputs).waveform

        audio = output[0].cpu().numpy()

        # 5. Peak Normalization & Soft-Limiting (-1.0 dB target)
        peak = np.max(np.abs(audio))
        if peak > 1e-4:
            target_peak = 0.89  # ~ -1.0 dBFS
            audio = (audio / peak) * target_peak

        return audio.astype(np.float32)

    def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        is_ipa: bool = False,
        speaking_rate: float = 1.2,
        noise_scale: float = 0.667,
        noise_scale_duration: float = 0.8,
    ) -> str:
        audio = self.synthesize(
            text=text,
            is_ipa=is_ipa,
            speaking_rate=speaking_rate,
            noise_scale=noise_scale,
            noise_scale_duration=noise_scale_duration,
        )
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        sf.write(output_path, audio, self.sample_rate)
        duration = len(audio) / self.sample_rate
        print(f"[NeuralSynthesizer] Generated '{output_path}' ({duration:.2f}s, {self.sample_rate} Hz)")
        return output_path


def main():
    parser = argparse.ArgumentParser(description="Universal Local Neural Speech Synthesizer")
    parser.add_argument("--text", "-t", type=str, help="Text or IPA phrase to synthesize")
    parser.add_argument("--file", "-f", type=str, help="Path to text or IPA input file")
    parser.add_argument("--ipa", action="store_true", help="Treat input explicitly as IPA phonetic notation")
    parser.add_argument("--speed", "--rate", type=float, default=1.2, help="Speaking rate / duration scaling factor (default: 1.2)")
    parser.add_argument("--noise-scale", type=float, default=0.667, help="Latent flow stochastic noise scale (default: 0.667)")
    parser.add_argument("--noise-scale-dur", type=float, default=0.8, help="Duration predictor stochastic noise scale (default: 0.8)")
    parser.add_argument("--output", "-o", type=str, default="output/neural_speech.wav", help="Output WAV file path")
    parser.add_argument("--device", type=str, default=None, help="Device: cuda or cpu (auto-detected by default)")
    parser.add_argument("--model", type=str, default="facebook/mms-tts-eng", help="HuggingFace model ID or local path")

    args = parser.parse_args()

    # Determine input text
    input_text = ""
    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            input_text = f.read().strip()
    elif args.text:
        input_text = args.text
    else:
        # Default benchmark
        input_text = "We saw you go."
        print(f"No text provided, using default benchmark phrase: '{input_text}'")

    synth = NeuralSynthesizer(model_id=args.model, device=args.device)
    synth.synthesize_to_file(
        text=input_text,
        output_path=args.output,
        is_ipa=args.ipa,
        speaking_rate=args.speed,
        noise_scale=args.noise_scale,
        noise_scale_duration=args.noise_scale_dur,
    )


if __name__ == "__main__":
    main()
