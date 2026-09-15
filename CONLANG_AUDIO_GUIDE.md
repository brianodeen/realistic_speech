# Constructed Language (Conlang) Audio Generation Guide

> **Vocalis Neural Speech Engine**  
> 100% Offline &bull; GPU-Accelerated (PyTorch + CUDA) &bull; Zero Cloud Dependencies &bull; ExtIPA Supported

This guide provides instructions on how to use the Vocalis speech synthesis engine to generate audio files (`.wav`) for constructed languages (such as *mraow*, alien dialects, fantasy tongues, and non-human vocalizations).

Because this engine operates on **phonetic sequences (IPA/ExtIPA)** rather than an English spelling dictionary, any pronounceable word or sound in your conlang can be synthesized naturally.

---

## 1. Quick Start: Single Word or Phrase

From the terminal in the `realistic_speech` folder, use `tools/neural_synthesizer.py`.

### A. Romanized Conlang Words
```bash
python tools/neural_synthesizer.py --text "mraow" --output output/mraow.wav
```

### B. International Phonetic Alphabet (IPA) Notation
Use the `--ipa` flag to pass exact phonetic symbols:
```bash
# Example: "wi sɔː ju ɡoʊ" ("We saw you go.")
python tools/neural_synthesizer.py --text "wi sɔː ju ɡoʊ" --ipa --output output/we_saw_you_go.wav

# Example with glottal stops [ʔ] and ejectives [kʼ]:
python tools/neural_synthesizer.py --text "kʼa ɬa ʔu" --ipa --output output/hunt_warning.wav
```

### C. Adjusting Cadence and Stochastic Expressiveness
- `--speed` (default `1.2`): Pacing multiplier. Use `0.9` for slow/solemn speech, `1.3` for rapid conversation.
- `--noise-scale` (default `0.667`): Governs pitch and inflection variance. Higher values (e.g. `0.85`) add more melodic fluctuation; lower values (e.g. `0.4`) produce steady, flat, or ritualistic chanting.
- `--noise-scale-dur` (default `0.8`): Governs rhythm and syllable timing randomness.

```bash
# Ritualistic chant (slower pace, lower pitch variance)
python tools/neural_synthesizer.py --text "om na ma shi va ya" --speed 0.95 --noise-scale 0.45 --output output/chant.wav

# Energetic conversation (faster pace, higher pitch variance)
python tools/neural_synthesizer.py --text "mraow shi aoo" --speed 1.35 --noise-scale 0.8 --output output/chat.wav
```

---

## 2. Batch Generation for Conlang Lexicons & Dictionaries

If your conlang project maintains a dictionary or phrasebook, you can generate all `.wav` audio files in a single batch command using `tools/batch_synthesize.py`.

### Supported File Formats
You can provide your lexicon as a `.csv`, `.json`, `.yaml`, or plain `.txt` file.

#### CSV Format (`lexicon.csv`)
```csv
id,ipa,meaning
greeting_casual,mraow,Informal friendly greeting
greeting_formal,wi sɔː ju ɡoʊ,Formal farewell blessing
warning_predator,kʼa ɬa ʔu,Danger from above
stealth_whisper,ʃiː ʔaʊ,Stay low and silent
purr_affection,ʬ̃ aː,Affectionate greeting
```

#### JSON Format (`lexicon.json`)
```json
[
  {"id": "greeting", "ipa": "mraow", "speed": 1.25},
  {"id": "farewell", "ipa": "wi sɔː ju ɡoʊ", "speed": 1.15},
  {"id": "warning", "ipa": "kʼa ɬa ʔu", "speed": 1.3}
]
```

#### Plain Text Format (`phrases.txt`)
```text
# id [TAB] text_or_ipa
word_01	mraow
word_02	kʼa ɬa ʔu
word_03	ʃiː ʔaʊ
```

### Running the Batch Command
```bash
python tools/batch_synthesize.py --lexicon path/to/your/lexicon.csv --output-dir ./generated_audio/
```

### Output:
1. Individual clean, volume-normalized `.wav` files for each entry:
   - `generated_audio/greeting_casual.wav`
   - `generated_audio/greeting_formal.wav`
   - `generated_audio/warning_predator.wav`
2. A machine-readable `manifest.json` linking every entry ID to its relative audio path, text, duration, and settings.

---

## 3. Python API: Integrating with Other Projects

If your conlang repository has its own Python scripts, web application, or game engine pipeline, you can import and call the synthesizer directly:

```python
import sys
# Add path to realistic_speech/tools if working in a separate repository
sys.path.append(r"C:\Users\brian\Documents\antigravity\realistic_speech\tools")

from neural_synthesizer import NeuralSynthesizer

# Initialize engine (loads model on RTX 5070 GPU or CPU)
synth = NeuralSynthesizer()

# Synthesize directly to a WAV file
synth.synthesize_to_file(
    text="wi sɔː ju ɡoʊ",
    output_path="audio/farewell.wav",
    is_ipa=True,
    speaking_rate=1.25,
    noise_scale=0.667
)

# Or generate float32 numpy audio array directly in memory
audio_data = synth.synthesize("mraow", speaking_rate=1.3)
# audio_data is a numpy array at 16,000 Hz sample rate
```

---

## 4. Phonetic & ExtIPA Reference for Conlang Authors

The engine automatically translates standard IPA and ExtIPA notation into phonemically accurate neural audio.

### Vowels & Glides
| IPA Symbol | Neural Representation | Example Pronunciation |
| :--- | :--- | :--- |
| `iː` / `i` | `ee` | As in *see*, *tree* |
| `ɪ` | `i` | As in *bit*, *sit* |
| `eɪ` | `ay` | As in *say*, *day* |
| `ɛ` | `e` | As in *bed*, *red* |
| `æ` | `a` | As in *cat*, *black* |
| `ɑː` / `aː` | `ah` | As in *father*, *calm* |
| `ɔː` / `ɔ` | `aw` | As in *saw*, *caught* |
| `oʊ` / `oː` | `oh` | As in *go*, *boat* |
| `uː` / `u` | `oo` | As in *you*, *moon* |
| `aɪ` | `eye` | As in *sky*, *light* |
| `aʊ` | `ow` | As in *now*, *how* |
| `y` / `ʏ` | `ue` | Close front rounded (German *über*, French *tu*) |
| `ø` / `œ` | `oe` | Close-mid front rounded (French *feu*, German *schön*) |

### Consonants & Articulatory Features
| IPA Symbol | Neural Representation | Description |
| :--- | :--- | :--- |
| `ʔ` | `'` (glottal stop) | Sudden vocal cord closure (as in *uh-oh*) |
| `kʼ`, `tʼ`, `pʼ` | `k'`, `t'`, `p'` | Ejective consonants (sharp glottalic airstream) |
| `ʃ` | `sh` | Postalveolar fricative (as in *she*) |
| `ʒ` | `zh` | Voiced postalveolar fricative (as in *vision*) |
| `θ` / `ð` | `th` | Dental fricatives (as in *thin* / *this*) |
| `ŋ` | `ng` | Velar nasal (as in *sing*) |
| `x` / `χ` | `kh` | Velar/uvular fricative (German *Bach*, Scots *loch*) |
| `ɬ` | `hl` | Voiceless alveolar lateral fricative (Welsh *ll*) |
| `ɮ` | `zl` | Voiced alveolar lateral fricative (Zulu *dl*) |
| `ɓ`, `ɗ`, `ɠ` | `b`, `d`, `g` | Implosive stops (ingressive air mechanics) |

### Chao Tones (Tonal Conlangs)
For tonal conlangs, you can attach Chao tone numbers (`1` to `5`) or IPA tone bars:
- `5` or `˥`: High tone
- `3` or `˧`: Mid tone
- `1` or `˩`: Low tone
- `51` or `˥˩`: High falling tone
- `15` or `˩˥`: Low rising tone

---

## 5. Web Studio & Interactive UI

To explore conlang scripts, adjust formant modulations, and preview acoustic parameters interactively, launch the studio server:

```bash
python run_studio.py
```
Open your web browser to:
```
http://localhost:8000
```
From the studio, you can:
- Select conlang presets (feline, canine, avian, predator, and human dialects).
- Edit YAML script blocks with visual feedback.
- Synthesize directly and export `.wav` audio.

---

## 6. How Other Projects Should Reference This Engine

When setting up a separate conlang repository, add this section to that repository's `README.md`:

```markdown
### Audio Generation
This language uses the **Vocalis Neural Speech Engine** to generate pronunciation audio.
To synthesize vocabulary audio for this project:

```bash
python C:/Users/brian/Documents/antigravity/realistic_speech/tools/batch_synthesize.py \
  --lexicon ./lexicon.csv \
  --output-dir ./audio/
```
```
