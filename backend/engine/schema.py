"""
Pydantic data models for the Universal Phonetic & Prosodic Conlang Script format,
and the low-level Parametric Spectral Sound Segment schema from the architectural specification.
Supports JSON and YAML serialization/deserialization with concise ExtIPA cursive strings.
"""

from typing import List, Optional, Union, Tuple, Dict, Any
from pydantic import BaseModel, Field


# ==============================================================================
# High-Level Phonetic Conlang Schema
# ==============================================================================

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
    chao_tone: Optional[str] = Field(default=None, description="Chao 5-level tone number, e.g., '55' (high flat), '35' (rising), '214' (dipping), '51' (falling)")
    pitch_curve: Optional[List[Tuple[float, float]]] = Field(
        default=None, 
        description="Explicit pitch curve spline points: [[time_ratio, f0_hz], ...]"
    )
    volume_envelope: Optional[List[Tuple[float, float]]] = Field(
        default=None,
        description="Volume dynamics curve points: [[time_ratio, db_offset], ...]"
    )
    phonation: str = Field(
        default="modal", 
        description="modal, breathy, creaky, ventricular_growl, whisper, falsetto, feline_purr, growl, purr, snarl"
    )
    vibrato_rate_hz: Optional[float] = Field(default=0.0, description="Vibrato rate in Hz (0 = none, typical 5-7Hz)")
    vibrato_depth_semitones: Optional[float] = Field(default=0.0, description="Vibrato depth in semitones")


class Syllable(BaseModel):
    id: Optional[str] = Field(default=None, description="Unique syllable identifier")
    label: str = Field(default="", description="Human-readable phonetic label (e.g., 'k͡rˠa', 'mǎ', 'grrr')")
    duration_ms: Optional[float] = Field(default=None, description="Total syllable duration (sum of phonemes if omitted)")
    prosody: ProsodyTrack = Field(default_factory=ProsodyTrack)
    phonemes: List[PhonemeSegment] = Field(default_factory=list)


class ExtIPAPhraseItem(BaseModel):
    phrase: Optional[str] = Field(default=None, description="ExtIPA phonetic string with cursive ties, e.g., 'kǀiː‿ʃuː'")
    tone: Optional[str] = Field(default=None, description="Chao tone string, e.g., '55', '51 35'")
    phonation: Optional[str] = Field(default="modal", description="modal, breathy, creaky, growl, purr, snarl, whisper")
    break_type: Optional[str] = Field(default=None, alias="break", description="'glottal_stop', 'pause', 'breath'")


class SpeakerProfile(BaseModel):
    name: str = Field(default="Conlang Speaker")
    voice_type: Optional[str] = Field(default="natural_male", description="'natural_male', 'natural_female', 'baritone', 'soprano', 'elder', 'deep_beast'")
    base_pitch_hz: float = Field(default=140.0, description="Base fundamental frequency F0 in Hz (100-300)")
    pitch_range_semitones: float = Field(default=12.0, description="Pitch range spanning Chao levels 1 to 5")
    vocal_tract_scale: float = Field(default=1.0, description="Vocal tract scaling: 1.0 (human)")
    speed_rate: float = Field(default=1.0, description="Speech rate multiplier (0.8 slower, 1.2 faster)")
    breathiness: float = Field(default=0.05, description="Global breathy noise mix (0.0 to 1.0)")
    vocal_fry: float = Field(default=0.0, description="Global vocal fry/creak mix (0.0 to 1.0)")
    growl_roughness: float = Field(default=0.0, description="Global ventricular growl roughness (0.0 to 1.0)")
    purr_depth: float = Field(default=0.0, description="Global feline purr gating depth (0.0 to 1.0)")
    cursive_flow: float = Field(default=0.85, description="Continuous cursive syllable/phoneme coarticulation blending (0.0 to 1.0)")
    acoustic_warmth: float = Field(default=0.40, description="Chest body warmth & analog saturation (0.0 to 1.0)")
    fleshiness: float = Field(default=0.70, description="Soft tissue damping, viscoelastic return phase, and anti-metallic smoothing (0.0 to 1.0)")
    default_volume_db: float = Field(default=0.0, description="Master volume trim in dB")


class ConlangScript(BaseModel):
    version: str = Field(default="2.0")
    language: str = Field(default="Universal Conlang")
    description: Optional[str] = Field(default="ExtIPA Phonetic Cursive Script")
    speaker: SpeakerProfile = Field(default_factory=SpeakerProfile)
    script: Optional[Union[str, List[str]]] = Field(default=None, description="Concise ExtIPA cursive text string, e.g. 'wiː‿sɔː juː‿ɡoʊ'")
    utterance: List[Union[Syllable, ExtIPAPhraseItem, Dict[str, Any]]] = Field(default_factory=list)


# ==============================================================================
# Low-Level Parametric Spectral Schema (Section 5 Architecture Specification)
# ==============================================================================

class BoundaryTransition(BaseModel):
    mode: str = Field(default="coarticulate", description="'coarticulate', 'glottal_stop', 'crossfade'")
    transition_duration_ms: float = Field(default=60.0)
    interpolation_curve: Optional[str] = Field(default="smootherstep", description="'linear', 'smoothstep', 'smootherstep'")
    glottal_silence_ms: Optional[float] = Field(default=20.0)
    glottal_pop_intensity: Optional[float] = Field(default=0.4)


class TrajectoryPoint(BaseModel):
    time_ratio: float = Field(..., ge=0.0, le=1.0)
    frequency_hz: float


class VibratoLFO(BaseModel):
    rate_hz: float = Field(default=5.5)
    depth_semitones: float = Field(default=0.5)
    onset_delay_ms: float = Field(default=100.0)


class ContinuousParameterTrack(BaseModel):
    anchor_points: List[TrajectoryPoint] = Field(default_factory=list)
    vibrato: Optional[VibratoLFO] = Field(default=None)
    cubic_tension: float = Field(default=0.0)


class VocalTractResonator(BaseModel):
    index: int = Field(..., ge=1, le=5)
    frequency_track: ContinuousParameterTrack
    bandwidth_hz: float = Field(default=90.0)
    gain_db: float = Field(default=0.0)


class AcousticSoundSegment(BaseModel):
    id: str
    symbol_ipa: str
    duration_ms: float
    boundary_in: BoundaryTransition = Field(default_factory=BoundaryTransition)
    boundary_out: BoundaryTransition = Field(default_factory=BoundaryTransition)
    f0_track: ContinuousParameterTrack
    volume_track: ContinuousParameterTrack
    formants: List[VocalTractResonator] = Field(default_factory=list)
    aspiration_noise_gain: float = Field(default=0.0)
    frication_noise_gain: float = Field(default=0.0)
    creature_mod_gain: float = Field(default=0.0)


class ParametricSpectralSequence(BaseModel):
    version: str = Field(default="1.0")
    audio_sample_rate: int = Field(default=44100)
    speaker_profile: SpeakerProfile = Field(default_factory=SpeakerProfile)
    timeline: List[AcousticSoundSegment] = Field(default_factory=list)
