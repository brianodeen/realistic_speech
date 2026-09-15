"""
ExtIPA and Conlang Phonetic Normalizer.
Translates ExtIPA phonetic sequences, non-pulmonic symbols, tones,
and constructed language orthography into phonemically clean representations
for neural speech synthesis.
"""

import re
from typing import Dict, List, Tuple

IPA_VOWEL_MAP = {
    "iː": "ee", "i": "ee", "ɪ": "i",
    "eː": "ay", "e": "eh", "ɛ": "e", "æ": "a",
    "aː": "ah", "a": "ah", "ɑː": "ah", "ɑ": "ah",
    "ɒ": "o", "ɔː": "aw", "ɔ": "aw",
    "oː": "oh", "o": "oh", "ʊ": "oo",
    "uː": "oo", "u": "oo", "ʌ": "u", "ə": "uh", "ɜː": "er", "ɜ": "er",
    "eɪ": "ay", "aɪ": "eye", "ɔɪ": "oy",
    "aʊ": "ow", "oʊ": "oh", "əʊ": "oh",
    "ɪə": "eer", "eə": "air", "ʊə": "oor",
    "y": "ue", "ʏ": "ue", "ø": "oe", "œ": "oe",
}

IPA_CONSONANT_MAP = {
    "p": "p", "b": "b", "t": "t", "d": "d",
    "k": "k", "ɡ": "g", "g": "g",
    "ʔ": "'", "ʡ": "'",
    "m": "m", "n": "n", "ŋ": "ng", "ɲ": "ny",
    "f": "f", "v": "v", "θ": "th", "ð": "th",
    "s": "s", "z": "z", "ʃ": "sh", "ʒ": "zh",
    "h": "h", "x": "kh", "χ": "kh", "ɣ": "gh",
    "tʃ": "ch", "dʒ": "j", "ts": "ts", "dz": "dz",
    "l": "l", "ɫ": "l", "r": "r", "ɾ": "r", "ɹ": "r", "ʀ": "r",
    "j": "y", "w": "w", "ʍ": "wh",
    "ɬ": "hl", "ɮ": "zl",
    "ɓ": "b", "ɗ": "d", "ɠ": "g",
    "pʼ": "p'", "tʼ": "t'", "kʼ": "k'", "sʼ": "s'",
}

CHAO_TONE_MAP = {
    "˥": "5", "˦": "4", "˧": "3", "˨": "2", "˩": "1",
}


def normalize_ipa_to_neural(ipa_text: str) -> str:
    """
    Converts raw IPA notation (e.g. 'wi sɔː ju ɡoʊ') to neural phonetic text.
    Handles multi-character diphthongs and affricates first, then single symbols.
    """
    text = ipa_text.strip()
    text = text.replace("ˈ", "").replace("ˌ", "")
    for chao, digit in CHAO_TONE_MAP.items():
        text = text.replace(chao, digit)
        
    all_maps = {**IPA_VOWEL_MAP, **IPA_CONSONANT_MAP}
    sorted_patterns = sorted(all_maps.keys(), key=lambda s: -len(s))
    
    words = text.split()
    output_words = []
    
    for word in words:
        w = word
        for symbol in sorted_patterns:
            target = all_maps[symbol]
            w = w.replace(symbol, target)
        w_clean = re.sub(r"[^a-zA-Z0-9'\- ]", "", w)
        if w_clean:
            output_words.append(w_clean.lower())
            
    return " ".join(output_words)


def prepare_conlang_utterance(text: str, is_ipa: bool = False) -> str:
    """
    Prepares any conlang input (orthographic or IPA) for synthesis.
    If text is already standard English/romanized text, lightly cleans it.
    If text contains IPA characters, parses and normalizes it.
    """
    ipa_indicators = set("ɔəɛɪʊʌæɑɒʃʒθðŋʔʡɲχɣɬɮɓɗɠˈˌː˥˦˧˨˩")
    has_ipa = is_ipa or any(c in ipa_indicators for c in text)
    
    if has_ipa:
        return normalize_ipa_to_neural(text)
    
    cleaned = re.sub(r"[^\w\s\',.!?\-]", "", text)
    return cleaned.strip()
