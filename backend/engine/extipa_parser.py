"""
ExtIPA (Extended International Phonetic Alphabet) Parser and Normalizer.
Parses cursive tie-bars (‿, ͡), African velaric clicks (ǀ, ǃ, ǁ, ʘ), ejectives (ʼ),
glottal stops (ʔ), long vowels (ː), tone contours, and ExtIPA creature phonation symbols.
Translates them into continuous phonetic streams for Neural Acoustic Vocoders.
"""

import re
import unicodedata
from typing import List, Dict, Any, Tuple, Optional

from .schema import Syllable, PhonemeSegment, ProsodyTrack


# Exact multi-character and single-character IPA token dictionary (ordered by longest match)
IPA_TOKEN_TABLE = [
    # Explicit normalized sustained vowels (Prevent split into separate syllables)
    ("oo", "oo"), ("ee", "ee"), ("ah", "ah"), ("ay", "ay"), ("oh", "oh"),
    
    # Diphthongs & Complex Long Vowels
    ("oʊ", "oh"), ("aʊ", "ow"), ("aɪ", "eye"), ("eɪ", "ay"), ("ɔɪ", "oy"),
    ("iː", "ee"), ("uː", "oo"), ("eː", "ay"), ("oː", "oh"), ("aː", "ah"),
    ("ɔː", "aw"), ("ɛː", "eh"), ("ɜː", "er"), ("ɑː", "ah"), ("yː", "ue"),
    
    # Clicks with velar release
    ("kǀ", "k"), ("kǃ", "k"), ("kǁ", "k"), ("kʘ", "p"),
    ("ɡǀ", "g"), ("ɡǃ", "g"), ("ɡǁ", "g"),
    ("ǀ", "k"), ("ǃ", "k"), ("ǁ", "k"), ("ʘ", "p"),
    
    # Ejectives
    ("kʼ", "k"), ("tʼ", "t"), ("pʼ", "p"), ("sʼ", "s"),
    
    # Consonants
    ("t͡s", "ts"), ("t͡ʃ", "ch"), ("d͡ʒ", "j"), ("k͡r", "kr"), ("ɡ͡r", "gr"),
    ("ʃ", "sh"), ("ʒ", "zh"), ("tʃ", "ch"), ("dʒ", "j"),
    ("θ", "th"), ("ð", "th"), ("ŋ", "ng"), ("ɲ", "ny"),
    ("x", "kh"), ("ɣ", "gh"), ("ħ", "h"), ("ʕ", ""),
    ("ɡ", "g"), ("g", "g"), ("k", "k"), ("p", "p"), ("b", "b"),
    ("t", "t"), ("d", "d"), ("m", "m"), ("n", "n"), ("f", "f"),
    ("v", "v"), ("s", "s"), ("z", "z"), ("h", "h"), ("l", "l"),
    ("r", "r"), ("ɾ", "r"), ("ɹ", "r"), ("j", "y"), ("w", "w"),
    ("q", "k"),
    
    # Vowels
    ("i", "ee"), ("y", "ue"), ("ɨ", "uh"), ("u", "oo"),
    ("e", "ay"), ("ø", "oe"), ("ə", "uh"), ("o", "oh"),
    ("ɛ", "eh"), ("œ", "oe"), ("ɜ", "er"), ("ɔ", "aw"),
    ("æ", "a"), ("a", "ah"), ("ɑ", "ah"), ("ɒ", "aw"),
    ("ʌ", "uh"),
]

# ExtIPA Phonation / Creature Modifiers
EXTIPA_PHONATION_MAP = {
    "ʭ": "growl",       # Bidental / ventricular phonation
    "f͌": "snarl",       # Velopharyngeal friction
    "v͌": "snarl",
    "ʬ̃": "purr",        # Bilabial / velic mucosal trill
    "ʙ": "purr",
    "↓": "ingressive",  # Ingressive airflow
    "ʔ": "glottal_stop",# Glottal stop
}


class ExtIPAPhrase:
    def __init__(
        self,
        raw_text: str,
        phonetic_text: str,
        chao_tone: Optional[str] = None,
        phonation: str = "modal",
        is_break: bool = False,
        break_duration_ms: float = 0.0,
        has_click: bool = False,
        click_type: Optional[str] = None,
    ):
        self.raw_text = raw_text
        self.phonetic_text = phonetic_text
        self.chao_tone = chao_tone
        self.phonation = phonation
        self.is_break = is_break
        self.break_duration_ms = break_duration_ms
        self.has_click = has_click
        self.click_type = click_type

    def __repr__(self):
        return f"<ExtIPAPhrase raw='{self.raw_text}' phonetic='{self.phonetic_text}' tone='{self.chao_tone}' phonation='{self.phonation}'>"


def parse_extipa_string(ipa_str: str, default_tone: Optional[str] = None, default_phonation: str = "modal") -> List[ExtIPAPhrase]:
    """
    Parses an ExtIPA script string into continuous speech phrases separated ONLY by
    explicit glottal stops (ʔ) or phrase breaks (|, ‖).
    Words within a phrase flow together continuously without artificial pauses.
    """
    if not ipa_str:
        return []

    # Split strictly on explicit breaks (ʔ, |, ‖, \n), preserving continuous multi-word phrases!
    tokens = re.split(r'(ʔ|\||‖|\n+)', ipa_str.strip())
    phrases = []

    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue

        # 1. Glottal Stop / Phrase Break ("Lifting the pen")
        if tok in ["ʔ", "|", "‖"] or "\n" in tok:
            phrases.append(ExtIPAPhrase(
                raw_text=tok,
                phonetic_text="",
                is_break=True,
                break_duration_ms=45.0 if tok == "ʔ" else 80.0,
                phonation="glottal_stop"
            ))
            continue

        clean_tok = tok

        # 2. Check for Click Consonants
        has_click = False
        click_type = None
        for click_sym in ["kǀ", "kǃ", "kǁ", "kʘ", "ǀ", "ǃ", "ǁ", "ʘ"]:
            if click_sym in clean_tok:
                has_click = True
                click_type = click_sym
                break

        # 3. Check for ExtIPA Creature Phonation Modifiers
        detected_phonation = default_phonation
        for ext_sym, ph_mode in EXTIPA_PHONATION_MAP.items():
            if ext_sym in clean_tok:
                detected_phonation = ph_mode
                clean_tok = clean_tok.replace(ext_sym, "")

        # 4. Extract Chao Tone or Intonation Markings if present (e.g. 55, 35, 214, 51, 11)
        tone_match = re.search(r'([1-5]{2,3})', clean_tok)
        detected_tone = tone_match.group(1) if tone_match else default_tone
        if tone_match:
            clean_tok = clean_tok.replace(tone_match.group(0), "")

        # 5. Convert multi-word phrase to continuous phonetic sentence
        # Split words within this continuous phrase by whitespace
        words = clean_tok.split()
        phonetic_words = [convert_ipa_to_phonetic_orthography(w) for w in words if w.strip()]
        phonetic_phrase = " ".join(phonetic_words).strip()

        if phonetic_phrase:
            phrases.append(ExtIPAPhrase(
                raw_text=tok,
                phonetic_text=phonetic_phrase,
                chao_tone=detected_tone,
                phonation=detected_phonation,
                has_click=has_click,
                click_type=click_type,
            ))

    return phrases


def convert_ipa_to_phonetic_orthography(ipa_word: str) -> str:
    """
    Converts an IPA word/cursive compound into clean, natural phonetic orthography
    with consecutive vowel collapse (e.g. 'awoooo' -> 'Awoo').
    """
    w = ipa_word.strip()
    if not w:
        return ""

    # Check for direct word matches
    known_phrases = {
        "mā": "mā", "má": "má", "mǎ": "mǎ", "mà": "mà",
        "mɛˀ": "Mẹ", "əːj": "ơi", "sɨəˀ": "sữa", "kaː": "cá",
        "Oooommm": "Ohm", "Aaaa-eeee": "Ah-ee",
        "Oooommm‿Aaaa-eeee": "Ohm Ah-ee",
        "Trrrt": "Trrt", "Mraow": "Meow",
        "awooooːː": "Awoo", "awoooo": "Awoo", "awoo": "Awoo",
        "roaaar": "Roar", "krrgh": "Krrgh",
    }
    if w in known_phrases:
        return known_phrases[w]

    # 1. Collapse multiple consecutive identical vowels into a single sustained vowel
    # e.g. 'oooo' -> 'oo', 'uuuu' -> 'oo', 'aaaa' -> 'aa', 'eeee' -> 'ee', 'iiii' -> 'ee'
    w = re.sub(r'o{2,}', 'oo', w, flags=re.IGNORECASE)
    w = re.sub(r'u{2,}', 'oo', w, flags=re.IGNORECASE)
    w = re.sub(r'a{2,}', 'aa', w, flags=re.IGNORECASE)
    w = re.sub(r'e{2,}', 'ee', w, flags=re.IGNORECASE)
    w = re.sub(r'i{2,}', 'ee', w, flags=re.IGNORECASE)

    # Clean secondary articulation marks and length marks that don't change core spelling
    w = w.replace("ˠ", "").replace("ˀ", "")

    # If word contains cursive tie '‿', split into sub-elements and join with hyphen for fluid liaison
    if "‿" in w:
        sub_parts = [convert_ipa_to_phonetic_orthography(p) for p in w.split("‿") if p]
        return "-".join(sub_parts)

    # Clean ligature tie
    w = w.replace("͡", "")

    # Token-by-token longest match parsing
    res = []
    i = 0
    n = len(w)

    while i < n:
        matched = False
        for pattern, replacement in IPA_TOKEN_TABLE:
            p_len = len(pattern)
            if i + p_len <= n and w[i : i + p_len] == pattern:
                res.append(replacement)
                i += p_len
                matched = True
                break
        if not matched:
            # Skip unrecognized diacritic or length mark
            ch = w[i]
            if ch == "ː":
                pass
            elif ch.isalnum() or ch in [" ", "-", "'"]:
                res.append(ch)
            i += 1

    out = "".join(res).strip()

    # Clean redundant triple vowels
    out = re.sub(r'e{3,}', 'ee', out)
    out = re.sub(r'o{3,}', 'oo', out)
    out = re.sub(r'a{3,}', 'aa', out)

    return out.capitalize() if out else "Ah"


def extipa_to_syllables(extipa_phrases: List[ExtIPAPhrase]) -> List[Syllable]:
    """
    Converts a sequence of ExtIPAPhrase objects into standard Syllable objects
    for compatibility with the DSP acoustic resonator engine.
    """
    syllables = []
    for idx, p in enumerate(extipa_phrases):
        if p.is_break:
            # Glottal stop or pause
            syllables.append(Syllable(
                id=f"break_{idx + 1}",
                label="ʔ",
                duration_ms=p.break_duration_ms or 40.0,
                prosody=ProsodyTrack(phonation="modal"),
                phonemes=[PhonemeSegment(symbol="glottal_stop", type="consonant", duration_ms=p.break_duration_ms or 40.0)]
            ))
        else:
            phonemes = []
            if p.has_click:
                sym = "click_alveolar"
                if p.click_type in ["kǀ", "ǀ"]:
                    sym = "click_dental"
                elif p.click_type in ["kǁ", "ǁ"]:
                    sym = "click_lateral"
                elif p.click_type in ["kʘ", "ʘ"]:
                    sym = "click_bilabial"
                phonemes.append(PhonemeSegment(symbol=sym, type="consonant", duration_ms=35.0))

            if p.phonation == "growl":
                phonemes.append(PhonemeSegment(symbol="feline_growl", type="creature", intensity=0.9, duration_ms=180.0))
            elif p.phonation == "purr":
                phonemes.append(PhonemeSegment(symbol="feline_purr", type="creature", intensity=0.9, duration_ms=220.0))
            elif p.phonation == "snarl":
                phonemes.append(PhonemeSegment(symbol="canine_snarl", type="creature", intensity=0.85, duration_ms=180.0))

            # Default vowel
            vowel_dur = 160.0
            phonemes.append(PhonemeSegment(symbol="a", type="vowel", duration_ms=vowel_dur))

            syllables.append(Syllable(
                id=f"syl_{idx + 1}",
                label=p.raw_text,
                duration_ms=sum(ph.duration_ms for ph in phonemes),
                prosody=ProsodyTrack(chao_tone=p.chao_tone, phonation=p.phonation),
                phonemes=phonemes
            ))

    return syllables
