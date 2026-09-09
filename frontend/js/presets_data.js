/**
 * Built-in Preset Library for Universal Phonetic Speech Studio.
 * Provides instant offline/synchronous preset loading.
 */
window.BUILTIN_PRESETS = [
  {
    "id": "alien_click_tonal",
    "name": "Xylos (Tonal Click Conlang)",
    "json_data": {
      "version": "2.0",
      "language": "Xylos (Tonal Click Conlang)",
      "description": "Human-pronounceable conlang utilizing African velaric suction clicks (dental [kǀ], alveolar [kǃ], lateral [kǁ]), cursive glides, and glottal breaks.",
      "speaker": {
        "name": "Kalo the Storyteller",
        "voice_type": "natural_male",
        "base_pitch_hz": 145.0,
        "speed_rate": 0.95
      },
      "utterance": [
        {
          "phrase": "kǀiː‿ʃuː",
          "tone": "51 35",
          "phonation": "modal"
        },
        {
          "break": "glottal_stop"
        },
        {
          "phrase": "kǃaː‿kǁuː",
          "tone": "214 55",
          "phonation": "modal"
        }
      ]
    }
  },
  {
    "id": "avian_songbird_syrinx",
    "name": "Aves (Songbird Syrinx Conlang)",
    "json_data": {
      "version": "2.0",
      "language": "Aves (Songbird Syrinx Conlang)",
      "description": "High-register whistled tones and rapid melodic glides.",
      "speaker": {
        "name": "Songbird",
        "voice_type": "soprano",
        "base_pitch_hz": 240.0
      },
      "script": "t͡siː‿wiː t͡siː‿wiː"
    }
  },
  {
    "id": "canine_pack_alert",
    "name": "Kavrok (Canine Conlang)",
    "json_data": {
      "version": "2.0",
      "language": "Kavrok (Canine Conlang)",
      "description": "Canine-inspired conlang with guttural velar stops, mucosal snarls, and glottal closures.",
      "speaker": {
        "name": "Garrow Alpha",
        "voice_type": "baritone",
        "base_pitch_hz": 135.0
      },
      "utterance": [
        {
          "phrase": "wʌf",
          "phonation": "snarl"
        },
        {
          "break": "glottal_stop"
        },
        {
          "phrase": "ɡˠarː‿awooooːː",
          "phonation": "modal"
        }
      ]
    }
  },
  {
    "id": "canine_wolf_pack_chorus",
    "name": "Wolf Pack (Chorus & Intonation)",
    "json_data": {
      "version": "2.0",
      "language": "Wolf Pack (Chorus & Intonation)",
      "description": "Intonation glides with deep chest resonance and sustained open howling vowels.",
      "speaker": {
        "name": "Timber Wolf Alpha",
        "voice_type": "baritone",
        "base_pitch_hz": 125.0
      },
      "script": "ɡˠarː‿wʌf! ʔawooooːː"
    }
  },
  {
    "id": "dragon_mythic_roar",
    "name": "Draconic (Mythic Colossal Conlang)",
    "json_data": {
      "version": "2.0",
      "language": "Draconic (Mythic Colossal Conlang)",
      "description": "Deep low-register throat chant with subharmonic rumble.",
      "speaker": {
        "name": "Ignis Colossus",
        "voice_type": "baritone",
        "base_pitch_hz": 65.0
      },
      "utterance": [
        {
          "phrase": "Krrgh",
          "phonation": "growl"
        },
        {
          "break": "glottal_stop"
        },
        {
          "phrase": "Roaaar",
          "phonation": "growl"
        }
      ]
    }
  },
  {
    "id": "feline_domestic_conversation",
    "name": "Meow-Lish (Domestic Felid Conlang)",
    "json_data": {
      "version": "2.0",
      "language": "Meow-Lish (Domestic Felid Conlang)",
      "description": "Human-pronounceable domestic feline vocal features: soft chitters, melodic meows, and purrs.",
      "speaker": {
        "name": "Mochi",
        "voice_type": "natural_female",
        "base_pitch_hz": 195.0
      },
      "utterance": [
        {
          "phrase": "Trrrt",
          "phonation": "purr"
        },
        {
          "break": "glottal_stop"
        },
        {
          "phrase": "Mraow",
          "phonation": "modal"
        },
        {
          "break": "glottal_stop"
        },
        {
          "phrase": "pʬ̃ərː",
          "phonation": "purr"
        }
      ]
    }
  },
  {
    "id": "feline_predator",
    "name": "Zha-Kari (Feline Predator Conlang)",
    "json_data": {
      "version": "2.0",
      "language": "Zha-Kari (Feline Predator Conlang)",
      "description": "Human-pronounceable predatory felid language featuring false-cord throat growls, soft rhythmic purr trills, and glottal breaks.",
      "speaker": {
        "name": "Vakkar Shadow-Stalker",
        "voice_type": "baritone",
        "base_pitch_hz": 135.0,
        "speed_rate": 0.9
      },
      "utterance": [
        {
          "phrase": "k͡rˠaː‿ʃuː",
          "phonation": "growl"
        },
        {
          "break": "glottal_stop"
        },
        {
          "phrase": "pʬ̃ərː",
          "phonation": "purr"
        }
      ]
    }
  },
  {
    "id": "human_arabic_guttural_pharyngeal",
    "name": "Arabic (Guttural & Pharyngeal Benchmark)",
    "json_data": {
      "version": "2.0",
      "language": "Arabic (Guttural & Pharyngeal Benchmark)",
      "description": "Deep uvular and pharyngeal consonants with open vowels: Qal, khab, rooh (/qal xab ruːħ/).",
      "speaker": {
        "name": "Hamed",
        "voice_type": "baritone",
        "base_pitch_hz": 120.0
      },
      "script": "qal xab ruːħ"
    }
  },
  {
    "id": "human_english_vowels_diphthongs",
    "name": "English (Cursive Vowel Glide Benchmark)",
    "json_data": {
      "version": "2.0",
      "language": "English (Cursive Vowel Glide Benchmark)",
      "description": "Demonstrates continuous cursive front-to-back human vowel glides: 'We saw you go' (/wiː‿sɔː juː‿ɡoʊ/).",
      "speaker": {
        "name": "Aria Voice",
        "voice_type": "natural_female",
        "base_pitch_hz": 175.0,
        "speed_rate": 1.0
      },
      "script": "wiː‿sɔː juː‿ɡoʊ"
    }
  },
  {
    "id": "human_tibetan_throat_singing",
    "name": "Tibetan Kargyraa (Throat Singing Benchmark)",
    "json_data": {
      "version": "2.0",
      "language": "Tibetan Kargyraa (Throat Singing Benchmark)",
      "description": "Subharmonic false-vocal-cord drone chant with overtone harmonic glides.",
      "speaker": {
        "name": "Lama Tenzin",
        "voice_type": "baritone",
        "base_pitch_hz": 68.0
      },
      "utterance": [
        {
          "phrase": "Oooommm",
          "phonation": "growl"
        },
        {
          "break": "breath"
        },
        {
          "phrase": "Aaaa-eeee",
          "phonation": "growl"
        }
      ]
    }
  },
  {
    "id": "human_vietnamese_glottal_tones",
    "name": "Vietnamese (Glottalized Tone Benchmark)",
    "json_data": {
      "version": "2.0",
      "language": "Vietnamese (Glottalized Tone Benchmark)",
      "description": "Complex tonal contours with glottal stops and creaky phonation: Mẹ ơi, sữa cá (/mɛˀ əːj sɨəˀ kaː/).",
      "speaker": {
        "name": "HoaiMy",
        "voice_type": "natural_female",
        "base_pitch_hz": 185.0
      },
      "script": "mɛˀ əːj sɨəˀ kaː"
    }
  },
  {
    "id": "mandarin_tonal_humanoid",
    "name": "Mandarin (4-Tone Benchmark)",
    "json_data": {
      "version": "2.0",
      "language": "Mandarin (4-Tone Benchmark)",
      "description": "Demonstrates four distinct tonal contours on standard vowel-consonant morphemes: mā má mǎ mà.",
      "speaker": {
        "name": "Xiaoxiao",
        "voice_type": "natural_female",
        "base_pitch_hz": 180.0
      },
      "script": "mā má mǎ mà"
    }
  },
  {
    "id": "predator_growl_to_howl",
    "name": "Apex Predator (Growl to Howl Transition)",
    "json_data": {
      "version": "2.0",
      "language": "Apex Predator (Growl to Howl Transition)",
      "description": "Transition from guttural false-cord growl through a sharp glottal stop into a long sustained howl glide.",
      "speaker": {
        "name": "Apex Beast",
        "voice_type": "baritone",
        "base_pitch_hz": 110.0
      },
      "utterance": [
        {
          "phrase": "k͡rˠaː",
          "phonation": "growl"
        },
        {
          "break": "glottal_stop"
        },
        {
          "phrase": "awooooːː",
          "phonation": "modal"
        }
      ]
    }
  }
];
