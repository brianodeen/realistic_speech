# JSON/YAML Phonetic & Creature Symbol to Extended IPA Reference Guide

This document maps all phonetic symbols, articulatory parameters, creature vocal features, and tone numbers used in the JSON/YAML script format to their corresponding **International Phonetic Alphabet (IPA)** and **Extended IPA (ExtIPA)** standards.

---

## 1. Vowels & Resonant Nuclei

| JSON/YAML Symbol | IPA / ExtIPA | Vowel Height | Vowel Backness | Rounding | Typical Formants ($F_1, F_2, F_3$) | Description / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `i` | [i] | Close | Front | Unrounded | 280, 2250, 2800 Hz | Close front unrounded (as in "see") |
| `y` | [y] | Close | Front | Rounded | 280, 1900, 2400 Hz | Close front rounded (French "tu", German "über") |
| `e` | [e] | Close-mid | Front | Unrounded | 400, 2000, 2600 Hz | Close-mid front unrounded (Spanish "fe") |
| `eps` | [ɛ] | Open-mid | Front | Unrounded | 550, 1750, 2500 Hz | Open-mid front (as in "bed") |
| `ae` | [æ] | Near-open | Front | Unrounded | 700, 1600, 2450 Hz | Near-open front (as in "cat") |
| `a` | [a] / [ä] | Open | Central/Front | Unrounded | 800, 1300, 2400 Hz | Open unrounded (as in "father") |
| `schwa` / `ax` | [ə] | Mid | Central | Unrounded | 500, 1500, 2500 Hz | Neutral mid-central schwa (as in "about") |
| `u` | [u] | Close | Back | Rounded | 300, 850, 2300 Hz | Close back rounded (as in "boot") |
| `o` | [o] | Close-mid | Back | Rounded | 450, 950, 2400 Hz | Close-mid back rounded (as in "boat") |
| `open_o` | [ɔ] | Open-mid | Back | Rounded | 580, 900, 2400 Hz | Open-mid back rounded (as in "thought") |
| `turn_m` / `high_back_unrounded` | [ɯ] | Close | Back | Unrounded | 300, 1350, 2350 Hz | Japanese "u", Korean "eu" |
| `nasal_a` | [ã] | Open | Central | Nasalized | 750, 1300, 2200 Hz | Open vowel with velic port open |
| `nasal_o` | [õ] | Close-mid | Back | Nasalized | 450, 900, 2100 Hz | Portuguese/French nasal 'o' |

---

## 2. Pulmonic Consonants

### Plosives & Stops
| JSON/YAML Symbol | IPA Symbol | Place of Articulation | Voicing | Acoustic Profile | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `p` | [p] | Bilabial | Voiceless | Brief silent closure + high-frequency burst | "pin" |
| `b` | [b] | Bilabial | Voiced | Low-frequency voice bar + burst | "bin" |
| `t` | [t] | Alveolar | Voiceless | Closure + high diffuse burst (~3.5-4kHz) | "tin" |
| `d` | [d] | Alveolar | Voiced | Voice bar + alveolar burst | "din" |
| `k` | [k] | Velar | Voiceless | Closure + mid compact burst (~1.5-2.5kHz) | "kin" |
| `g` | [g] | Velar | Voiced | Voice bar + velar burst | "give" |
| `q` | [q] | Uvular | Voiceless | Deep guttural back stop burst | Arabic "qaf" |
| `glottal_stop` / `q_glottal` | [ʔ] | Glottal | Voiceless | Sudden complete vocal fold closure | "uh-oh" [ʔʌʔoʊ] |

### Fricatives & Sibilants
| JSON/YAML Symbol | IPA Symbol | Place of Articulation | Voicing | Acoustic Profile | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `f` | [f] | Labiodental | Voiceless | Low-amplitude flat high turbulence | "fin" |
| `v` | [v] | Labiodental | Voiced | Voiced periodic source + turbulence | "vine" |
| `th_voiceless` | [θ] | Dental | Voiceless | Diffuse high turbulence | "thin" |
| `th_voiced` | [ð] | Dental | Voiced | Voiced dental fricative | "this" |
| `s` | [s] | Alveolar | Voiceless | Intense high-frequency hiss (>4.5kHz) | "sin" |
| `z` | [z] | Alveolar | Voiced | Voiced alveolar sibilant | "zoo" |
| `sh` | [ʃ] | Postalveolar | Voiceless | Broad mid-frequency turbulence (~2.5-5kHz) | "shin" |
| `zh` | [ʒ] | Postalveolar | Voiced | Voiced postalveolar sibilant | "measure" |
| `x_velar` | [x] | Velar | Voiceless | Rough velar friction (~1.2-2.5kHz) | German "Bach", Scots "loch" |
| `gamma` | [ɣ] | Velar | Voiced | Voiced velar friction | Spanish "fuego" [ɣ] |
| `h` | [h] | Glottal | Voiceless | Aperiodic aspiration cavity resonance | "hat" |
| `h_voiced` | [ɦ] | Glottal | Voiced | Breathy voiced glottal transition | "ahead" |
| `hiss_feline` | [ʩ] / [h_cat] | Epiglottal/Velar | Voiceless | Extended high-intensity dual-constriction hiss | Feline defensive hiss |

### Nasals, Liquids & Trills
| JSON/YAML Symbol | IPA Symbol | Place | Voicing | Acoustic Profile | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `m` | [m] | Bilabial | Voiced | Low nasal murmur (~250Hz) | "man" |
| `n` | [n] | Alveolar | Voiced | Low nasal murmur + alveolar antiresonance | "no" |
| `ng` | [ŋ] | Velar | Voiced | High nasal murmur | "sing" |
| `l` | [l] | Alveolar Lateral | Voiced | Clean low formants with lateral antiformants | "let" |
| `r_tap` | [ɾ] | Alveolar Tap | Voiced | Ultra-brief closure (~20-30ms) | Spanish "pero", US "water" |
| `r_trill` | [r] | Alveolar Trill | Voiced | 3-5 rapid tongue-tip strikes (~25Hz) | Spanish "perro", Italian "rosso" |
| `uvular_trill` | [ʀ] | Uvular Trill | Voiced | Deep uvula vibration (~18-22Hz) | French/German r |

---

## 3. Non-Pulmonic & Conlang Consonants (Clicks, Ejectives, Implosives)

| JSON/YAML Symbol | IPA Symbol | Category | Airstream Mechanism | Acoustic Profile |
| :--- | :--- | :--- | :--- | :--- |
| `click_bilabial` | [ʘ] | Click | Lingual Ingressive | Soft lip-smack click, low-mid resonance |
| `click_dental` | [ǀ] | Click | Lingual Ingressive | Sharp high "tsk-tsk" suction burst |
| `click_alveolar` | [ǃ] | Click | Lingual Ingressive | Loud, hollow "pop" sound with low-frequency resonance |
| `click_lateral` | [ǁ] | Click | Lingual Ingressive | Side-tongue suction pop (horse-clicking) |
| `ejective_k` | [kʼ] | Ejective | Glottalic Egressive | Velar burst immediately followed by abrupt glottal closure |
| `ejective_t` | [tʼ] | Ejective | Glottalic Egressive | Sharp alveolar snap + glottal silence |
| `ejective_p` | [pʼ] | Ejective | Glottalic Egressive | Bilabial pop + glottal closure |
| `implosive_b` | [ɓ] | Implosive | Glottalic Ingressive | Pre-voiced lowering larynx "glug" effect |
| `implosive_d` | [ɗ] | Implosive | Glottalic Ingressive | Suction-voiced alveolar stop |

---

## 4. Feline & Canine Bioacoustic Vocal Modules

These creature vocalizations are represented as dedicated acoustic blocks or phonation modifiers within syllables:

| JSON/YAML Symbol | ExtIPA / Phonetic Equivalent | Bioacoustic Mechanism | Controllable Acoustic Parameters | Description |
| :--- | :--- | :--- | :--- | :--- |
| `feline_purr` | [ʬ̃_purr] / ExtIPA [!˭] | 20–28 Hz rhythmic laryngeal neural twitch gating respiration | `rate_hz` (20-30), `depth` (0.0-1.0), `ingressive_ratio` | Low-frequency rhythmic rumbling purr modulating phonemes |
| `feline_growl` | [ʭ_growl] / [ɣ_ventricular] | Subharmonic ventricular (false vocal cord) vibration + deep pharynx resonance | `intensity` (0.0-1.0), `subharmonic_ratio` (0.5=octave below), `roughness` | Threatening guttural feline throat growl |
| `feline_chitter` | [ǂ_chitter] | Rapid jaw-chattering (12-16Hz) with high-pitch dental clicks | `chatter_rate` (10-18Hz), `chirp_f0` (1-3kHz) | Hunting chitter / excitement chirps |
| `feline_hiss` | [ʩ_hiss] | Velic/pharyngeal turbulent jet with tongue arching | `intensity`, `cutoff_khz` (3-8kHz) | Sharp defensive hiss |
| `canine_snarl` | [r_snarl] | Upper-lip retraction + laryngeal flutter + rough friction | `lip_curl` (brightens formants), `flutter_hz` (40-60Hz) | Aggressive canine snarl with lip curl |
| `canine_bark` | [ʔ_bark] / [b_chest] | Sudden chest-compression burst + fast decaying pitch drop | `impact_power`, `body_resonance_hz`, `decay_ms` | Sharp acoustic bark / warning yip |
| `canine_whine` | [i_whine] | High-register falsetto sine-harmonic with frequency glide | `pitch_hz` (600-2500Hz), `jitter`, `glide_slope` | Submissive/excitement high pitch whine |
| `canine_howl` | [o_howl] / [u_howl] | Open acoustic tract, resonant fundamental sweep + vibrato | `base_f0` (250-600Hz), `vibrato_depth`, `vibrato_rate` | Long sustained resonant howl |

---

## 5. Prosody, Chao Tones & Phonation Modes

### 5-Level Chao Tone Representation (Chinese / Tonal Conlangs)
Tone contours are specified using the standard 1 to 5 scale ($1 = \text{lowest pitch}$, $5 = \text{highest pitch}$):

| Chao Tone Code | Pitch Contour | Description | Real-World Equivalent |
| :--- | :--- | :--- | :--- |
| `55` | High Level ($5 \to 5$) | Constant high pitch | Mandarin Tone 1 (mā 妈) |
| `35` | High Rising ($3 \to 5$) | Medium start sweeping up | Mandarin Tone 2 (má 麻) |
| `214` | Dipping ($2 \to 1 \to 4$) | Low dip then rising | Mandarin Tone 3 (mǎ 马) |
| `51` | High Falling ($5 \to 1$) | Sharp dramatic drop | Mandarin Tone 4 (mà 骂) |
| `33` | Mid Level ($3 \to 3$) | Sustained mid pitch | Cantonese Tone 3 |
| `21` | Low Falling ($2 \to 1$) | Low subtle descent | Cantonese Tone 4 |
| `11` | Low Level ($1 \to 1$) | Deep steady base pitch | Vietnamese Huyền tone |

### Phonation Modes (`phonation`)
| JSON Value | ExtIPA Diacritic | Physical Acoustic Characteristic |
| :--- | :--- | :--- |
| `modal` | — | Normal clean vocal fold vibration |
| `breathy` | [ạ] / [a̤] | Vocal folds do not close completely; high aperiodic airflow |
| `creaky` / `vocal_fry` | [a̰] | Highly compressed, low-rate irregular subharmonic pulses (~40-70Hz) |
| `ventricular_growl` | [a᷽] | False vocal cords vibrate simultaneously with true folds (death growl/throat singing) |
| `whisper` | [ḁ] | Purely turbulent aperiodic noise filtered through vocal tract |
| `falsetto` | [a_falsetto] | High-pitch thin-margin vocal fold oscillation |
