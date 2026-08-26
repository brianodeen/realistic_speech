"""
Pydantic data models for the Universal Phonetic & Prosodic Conlang Script format.
Supports JSON and YAML serialization/deserialization.
"""

from typing import List, Optional, Union, Tuple, Dict, Any
from pydantic import BaseModel, Field


class PhonemeSegment(BaseModel):
    symbol: str = Field(..., description="Phonetic or creature symbol, e.g., 'k', 'a', 'feline_growl', 'click_alveolar'")
    type: str = Field(default="vowel", description="Segment type: 'vowel', 'consonant', 'creature', 'pause'")
    duration_ms: float = Field(default=100.0, description="Duration of this segment in milliseconds")
    
    # Articulatory details (optional overrides)
    manner: Optional[str] = Field(default=None, description="plosive, fricative, nasal, approximant, trill, click, ejective, implosive")
    place: Optional[str] = Field(default=None, description="bilabial, alveolar, velar, uvular, pharyngeal, glottal, etc.")
    voicing: Optional[bool] = Field(default=None, description="True for voiced, False for voiceless")
    airstream: Optional[str] = Field(default="pulmonic", description="pulmonic, ejective, implosive, click")
    
    # Vowel features
    vowel_height: Optional[str] = Field(default=None, description="close, close-mid, open-mid, open")
    vowel_backness: Optional[str] = Field(default=None, description="front, central, back")
    rounding: Optional[bool] = Field(default=False)
    nasal: Optional[bool] = Field(default=False)
    
    # Creature parameters (when type == 'creature')
    category: Optional[str] = Field(default=None, description="feline_growl, feline_purr, feline_hiss, feline_chitter, canine_snarl, canine_bark, canine_whine, canine_howl")
    intensity: Optional[float] = Field(default=0.8, description="0.0 to 1.0 creature modulation intensity")
    subharmonic_depth: Optional[float] = Field(default=0.5, description="Depth of subharmonic throat vibration (0.0 to 1.0)")
    rate_hz: Optional[float] = Field(default=None, description="Specific modulation rate (e.g. 25Hz for purr, 50Hz for snarl)")
    extra_params: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProsodyTrack(BaseModel):
    # Tone representation: 5-level Chao tone string (e.g., '55', '35', '214', '51', '11')
    chao_tone: Optional[str] = Field(default=None, description="Chao 5-level tone number, e.g., '55' (high flat), '35' (rising), '214' (dipping), '51' (falling)")
    
    # Continuous pitch curve: list of [time_ratio (0.0 to 1.0), pitch_hz or relative_semitone]
    pitch_curve: Optional[List[Tuple[float, float]]] = Field(
        default=None, 
        description="Explicit pitch curve spline points: [[time_ratio, f0_hz], ...]"
    )
    
    # Volume dynamics curve: list of [time_ratio (0.0 to 1.0), db_offset (-24.0 to +6.0)]
    volume_envelope: Optional[List[Tuple[float, float]]] = Field(
        default=None,
        description="Volume dynamics curve points: [[time_ratio, db_offset], ...]"
    )
    
    # Phonation mode
    phonation: str = Field(
        default="modal", 
        description="modal, breathy, creaky, ventricular_growl, whisper, falsetto, feline_purr"
    )
    
    # Micro-prosody vibrato/tremolo
    vibrato_rate_hz: Optional[float] = Field(default=0.0, description="Vibrato rate in Hz (0 = none, typical 5-7Hz)")
    vibrato_depth_semitones: Optional[float] = Field(default=0.0, description="Vibrato depth in semitones")


class Syllable(BaseModel):
    id: Optional[str] = Field(default=None, description="Unique syllable identifier")
    label: str = Field(default="", description="Human-readable phonetic label (e.g., 'k͡rˠa', 'mǎ', 'grrr')")
    duration_ms: Optional[float] = Field(default=None, description="Total syllable duration (sum of phonemes if omitted)")
    prosody: ProsodyTrack = Field(default_factory=ProsodyTrack)
    phonemes: List[PhonemeSegment] = Field(default_factory=list)


class SpeakerProfile(BaseModel):
    name: str = Field(default="Conlang Speaker")
    base_pitch_hz: float = Field(default=140.0, description="Base fundamental frequency F0 in Hz (100-300)")
    pitch_range_semitones: float = Field(default=12.0, description="Pitch range spanning Chao levels 1 to 5")
    vocal_tract_scale: float = Field(default=1.0, description="Vocal tract scaling: < 1.0 (smaller/feline), 1.0 (human), > 1.0 (canine/beast)")
    breathiness: float = Field(default=0.05, description="Global breathy noise mix (0.0 to 1.0)")
    vocal_fry: float = Field(default=0.0, description="Global vocal fry/creak mix (0.0 to 1.0)")
    growl_roughness: float = Field(default=0.0, description="Global ventricular growl roughness (0.0 to 1.0)")
    purr_depth: float = Field(default=0.0, description="Global feline purr gating depth (0.0 to 1.0)")
    cursive_flow: float = Field(default=0.85, description="Continuous cursive syllable/phoneme coarticulation blending (0.0 to 1.0)")
    acoustic_warmth: float = Field(default=0.40, description="Chest body warmth & analog saturation (0.0 to 1.0)")
    fleshiness: float = Field(default=0.70, description="Soft tissue damping, viscoelastic return phase, and anti-metallic smoothing (0.0 to 1.0)")
    default_volume_db: float = Field(default=0.0, description="Master volume trim in dB")


class ConlangScript(BaseModel):
    version: str = Field(default="1.0")
    language: str = Field(default="Universal Conlang")
    description: Optional[str] = Field(default="Phonetic & prosodic conlang script")
    speaker: SpeakerProfile = Field(default_factory=SpeakerProfile)
    utterance: List[Syllable] = Field(default_factory=list)
