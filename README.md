# Universal Phonetic Speech Studio

A synthesis system and interactive web visual studio designed to produce realistic speech in **any language (including constructed/artificial languages)** with **animal & creature vocal features** (feline growls, purrs, canine snarls, barks, whines) and **fine-grained micro-prosody** (Chinese-style Chao 5-level tones, Bézier pitch splines, volume dynamics, and phonation modes).

---

## Key Features

1. **Portable JSON / YAML Phonetic Script Schema**:
   - Clean, human- and machine-readable conlang scripting format.
   - Decomposes speech into articulatory feature vectors, decoupling phonetic segments from prosodic intonation.
   - Full mapping to **Extended IPA (ExtIPA)** provided in [`phonetic_symbol_reference.md`](file:///c:/Users/brian/Documents/antigravity/realistic_speech/phonetic_symbol_reference.md).

2. **Bioacoustic & Creature Vocalization Engine**:
   - **Feline Purrs**: 24.5 Hz rhythmic laryngeal neural twitch oscillator with alternating respiratory gating.
   - **Feline Throat Growls**: Subharmonic ventricular (false vocal cord) vibration at $F_0/2$ & $F_0/3$ with guttural pharyngeal resonance.
   - **Feline Hisses**: High-energy dual-peak turbulent jets (3.5–7.5 kHz).
   - **Canine Snarls**: 48 Hz mucosal lip-curl flutter with brightened upper formants.
   - **Canine Warning Barks**: Chest-impact impulse with steep decaying pitch contours.
   - **Canine Whines & Howls**: High-register falsetto harmonics with sweeping glides.

3. **Deterministic Tone & Intonation Control**:
   - **5-Level Chao Tone Numbers**: `55` (High Level), `35` (High Rising), `214` (Dipping), `51` (High Falling), `33` (Mid), `11` (Deep Base).
   - **Arbitrary Bézier Pitch Splines**: Exact point-by-point fundamental frequency ($F_0$) trajectory drawing.
   - **Dynamic Volume Envelopes**: Decibel/RMS dynamics per phoneme/syllable.
   - **Phonation Modes**: `modal`, `breathy` [ạ], `creaky/fry` [a̰], `ventricular_growl` [a᷽], `whisper` [ḁ], `falsetto`.

4. **Interactive Web Visual Studio**:
   - **Timeline Sequencer**: Visual syllable and phoneme block tracks with duration resizing.
   - **Tone & Pitch Canvas**: Interactive Bézier spline editor with Chao grid overlay and instant tone presets.
   - **Bi-Directional Code Editor**: Live YAML/JSON editor with syntax validation and instant 2-way UI sync.
   - **Real-Time Spectrogram & FFT Player**: Live audio synthesis, animated playhead, and 44.1kHz WAV export.
   - **Phonetic Palette**: 50+ searchable sound chips (Vowels, Consonants, Clicks, Ejectives, Creature vocalizations).

---

## Quickstart

### 1. Requirements
Ensure Python 3.10+ is installed with dependencies:
```bash
pip install -r requirements.txt
```
*(Dependencies: `fastapi`, `uvicorn`, `scipy`, `soundfile`, `pyyaml`, `pydantic`)*

### 2. Launching the Studio
Run the launcher script:
```bash
python run_studio.py
```
This automatically starts the local backend server at `http://127.0.0.1:8000` and launches the visual studio in your default browser.

### 3. Running Verification Unit Tests
To test the acoustic engine across all presets and symbol tables:
```bash
python test_engine.py
```

---

## Project Structure

```
realistic_speech/
├── run_studio.py                      # One-click launcher script
├── test_engine.py                     # Acoustic engine unit tests
├── requirements.txt                   # Dependency list
├── phonetic_symbol_reference.md       # JSON/YAML to Extended IPA reference guide
├── backend/
│   ├── app.py                         # FastAPI REST & WebSocket server
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── schema.py                  # Pydantic data models for conlang scripts
│   │   ├── articulatory.py            # Phonetic lookup tables, formants, IPA mappings
│   │   ├── glottal.py                 # Rosenberg/LF glottal pulses, vocal fry, breathiness
│   │   ├── bioacoustics.py            # Feline purr/growl/hiss, canine snarl/bark/whine/howl
│   │   ├── prosody.py                 # Chao 5-level tones, Bézier pitch splines, volume envelopes
│   │   ├── tract.py                   # Time-varying digital formant filter cascade (F1-F5)
│   │   └── synthesizer.py             # Master 44.1kHz synthesis pipeline
│   └── presets/                       # Conlang script presets
│       ├── feline_predator.yaml
│       ├── canine_pack_alert.yaml
│       ├── alien_click_tonal.yaml
│       └── mandarin_tonal_humanoid.yaml
└── frontend/
    ├── index.html                     # Studio layout
    ├── css/
    │   └── studio.css                 # Dark pro-audio theme
    └── js/
        ├── app.js                     # Master frontend coordinator
        ├── timeline.js                # Syllable & phoneme sequencer
        ├── pitch_canvas.js            # Tone & pitch contour spline canvas
        ├── visualizer.js              # Real-time spectrogram & FFT visualizer
        ├── webaudio_synth.js          # Client-side audio previewer
        └── yaml_sync.js               # Bi-directional YAML/JSON sync
```
