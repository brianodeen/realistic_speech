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
├── vocalis_engine/                    # VocalisEngine: C++20 Biomechanical Acoustic Engine
│   ├── CMakeLists.txt                 # CMake configuration
│   ├── include/vocalis/               # Master headers & public API
│   │   ├── types.hpp                  # Sample types & C2 smootherstep
│   │   ├── vocalis.hpp                # Umbrella header
│   │   ├── dsp/                       # Biquads, PolyBLEP, Splines, Noise
│   │   ├── orchestra/                 # The 6 anatomical instruments & Conductor
│   │   ├── extipa/                    # ExtIPA parser, target DB & cursive compounder
│   │   ├── voice/                     # Speaker profiles & presets
│   │   └── platform/                  # Zero-dependency WAV file writer
│   ├── src/                           # Engine implementation files
│   ├── apps/                          # vocalis_cli standalone tool
│   ├── benchmarks/                    # High-throughput RTF benchmark (300x+ RTF)
│   └── tests/                         # Unit tests (DSP, parser, coarticulation)
├── documents/
│   ├── ground_up_cpp_speech_engine_specification.md # Architectural specification
│   └── parametric_spectral_synthesis_architecture.md
├── run_studio.py                      # One-click launcher script for web visual studio
├── test_engine.py                     # Python acoustic engine unit tests
├── requirements.txt                   # Dependency list
├── phonetic_symbol_reference.md       # JSON/YAML to Extended IPA reference guide
├── backend/                           # Python FastAPI REST & WebSocket server
└── frontend/                          # Interactive Pro-Audio Web Visual Studio
```

---

## VocalisEngine (C++20 Native Engine)

A first-principles biomechanical and organological acoustic speech engine ("Anatomy as an Orchestra of Instruments") running with zero third-party dependencies, featuring continuous $C^2$ Hermite smootherstep cursive coarticulation, LF-model glottal excitation, African velaric clicks, and creature bioacoustics.

### Building VocalisEngine

Requires a modern C++20 compiler (MSVC 2022/2026, GCC 11+, or Clang 13+):

```bash
# Configure build
cmake -B vocalis_engine/build -S vocalis_engine

# Build Release binaries
cmake --build vocalis_engine/build --config Release
```

### Running Tests & Benchmarks

```bash
# Run unit tests
./vocalis_engine/build/Release/test_dsp.exe
./vocalis_engine/build/Release/test_parser.exe
./vocalis_engine/build/Release/test_coarticulation.exe

# Run real-time factor benchmark (>300x real-time performance)
./vocalis_engine/build/Release/synthesis_benchmark.exe
```

### Command-Line Speech Synthesis (CLI)

```bash
# Synthesize human speech from ExtIPA
./vocalis_engine/build/Release/vocalis_cli.exe -i "m-a-m-a" -o mama.wav

# Synthesize creature vocalization (feline purrs, clicks, growls)
./vocalis_engine/build/Release/vocalis_cli.exe -i "[ǀ] uː ʬ̃ ʭ" -p feline -o beast.wav
```

---

## Objective Speech & Roboticness Audio Analyzer

An automated signal-processing-based acoustic evaluator (`analyze_speech.py` / `tools/analyze_speech.py`) that objectively scores audio for naturalness, roboticness, click/impulse artifacts, formant prominence, and bioacoustic features.

### Usage

```bash
# Detailed terminal scorecard audit of a speech file
python analyze_speech.py we_saw_you_go.wav

# Side-by-side comparative analysis of two audio files
python analyze_speech.py --compare file1.wav file2.wav

# Batch audit across an entire phrasebook directory
python analyze_speech.py --batch path/to/phrasebook_wavs/

# Machine-readable JSON metrics for CI/CD pipelines
python analyze_speech.py we_saw_you_go.wav --json
```

### Metrics Evaluated

- **Roboticness Index (0 to 100)**: Evaluates $F_0$ pitch monotony, pitch discontinuities, harmonic buzz index, and lack of natural micro-prosody. (Lower is better).
- **Human Naturalness Score (0 to 100)**: Measures continuous pitch contour, sentence declination, natural jitter (0.5%–2%) & shimmer (2%–5%), and formant contrast. (Higher is better).
- **Artifact Cleanliness (0 to 100)**: Detects impulsive clicks, high-frequency kurtosis spikes, and sample-to-sample derivative cliffs ($|\Delta s| > 0.15$).
- **Bioacoustic Phonetics**: Detects 20–30 Hz feline purr amplitude modulation, 40–55 Hz canine snarl tremor, ventricular growl subharmonics ($F_0/2$), and velaric suction clicks.

