"""
Universal Phonetic Speech Synthesis Package.
"""

from .schema import ConlangScript, Syllable, PhonemeSegment, SpeakerProfile, ProsodyTrack
from .synthesizer import synthesize_script, audio_to_wav_bytes, SAMPLE_RATE
from .neural_synthesizer import synthesize_neural_script, synthesize_neural_script_async
from .articulatory import get_all_symbols_metadata, VOWEL_TABLE, CONSONANT_TABLE, CREATURE_TABLE
