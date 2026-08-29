"""
Unit test script to verify conlang speech synthesis engine.
"""

import os
import glob
import yaml
import numpy as np

from backend.engine import ConlangScript, synthesize_script, audio_to_wav_bytes, get_all_symbols_metadata


def test_presets():
    preset_files = glob.glob("backend/presets/*.yaml")
    print(f"Found {len(preset_files)} presets: {preset_files}")
    assert len(preset_files) >= 4, "Expected at least 4 presets"

    for p_path in preset_files:
        print(f"\n--- Testing Preset: {p_path} ---")
        with open(p_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        script = ConlangScript(**data)
        assert script.utterance or script.script, f"Utterance/script empty in {p_path}"
        
        audio, telemetry = synthesize_script(script)
        
        # Verify assertions
        assert len(audio) > 0, "Audio array is empty"
        assert not np.isnan(audio).any(), "Audio contains NaN values"
        assert not np.isinf(audio).any(), "Audio contains Inf values"
        assert np.max(np.abs(audio)) <= 1.0, "Audio exceeds 1.0 peak"
        
        wav_bytes = audio_to_wav_bytes(audio)
        assert len(wav_bytes) > 44, "WAV byte stream is invalid"
        
        print(f"  Success! Duration: {telemetry['duration_sec']:.2f}s, Audio Samples: {len(audio)}, WAV Size: {len(wav_bytes)} bytes")


def test_symbols_metadata():
    print("\n--- Testing Symbol Metadata Extraction ---")
    symbols = get_all_symbols_metadata()
    print(f"Extracted {len(symbols)} symbol definitions.")
    assert len(symbols) > 20, "Expected >20 symbols"
    
    creature_symbols = [s for s in symbols if s["category"] == "creature"]
    print(f"Found creature symbols: {[s['symbol'] for s in creature_symbols]}")
    assert len(creature_symbols) >= 6, "Expected at least 6 creature symbols"
    print("  Symbol metadata check passed!")


if __name__ == "__main__":
    test_symbols_metadata()
    test_presets()
    print("\n==========================================")
    print("  ALL SYNTHESIS ENGINE TESTS PASSED!  ")
    print("==========================================")
