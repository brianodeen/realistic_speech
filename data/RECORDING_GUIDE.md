# Personal Voice Recording Guide for Vocalis

This guide will help you record clean voice samples for training and fine-tuning your custom personal voice profile in Vocalis.

---

## 1. Quick Setup & Best Practices
- **Microphone**: Any USB condenser mic, headset mic, or smartphone voice memo recorder in a quiet room works great.
- **Environment**: Avoid rooms with echo (tile, bare walls). A bedroom with carpet, curtains, or pillows provides great acoustic absorption.
- **Distance**: Maintain a consistent 6–8 inches (15–20 cm) distance from the microphone.
- **Format**: WAV or MP3 (any sample rate, 44.1kHz or 48kHz is standard).
- **Target Quantity**:
  - **Quick Adaptation**: 15–30 short clips (approx. 2–5 minutes of total speaking).
  - **Deep Voice Fidelity**: 50–100 clips (approx. 8–15 minutes).

---

## 2. Directory Structure
Save your audio files in:
```
realistic_speech/
  data/
    my_voice_raw/
      sample_001.wav
      sample_002.wav
      ...
```

Once saved, simply run:
```bash
python tools/voice_cloner.py --prepare
```
The tool will automatically:
1. Resample to 16 kHz mono.
2. Trim leading/trailing room silence.
3. Normalize amplitude to standard studio level (-1.0 dBFS).
4. Verify duration and RMS clarity.

---

## 3. Recommended Prompts to Read

Read each sentence naturally at your normal conversational pace.

### Benchmark & Conversational
1. *"We saw you go."*
2. *"The sun rose slowly over the distant blue hills."*
3. *"Can you hear the difference in this voice profile?"*
4. *"Step into the garden and tell me what you see."*
5. *"Every journey begins with a single curious step."*

### Phonetically Balanced Sentences (Covers English & Conlang Transitions)
6. *"The quick brown fox jumps over the lazy dog."*
7. *"Oak is strong and also gives shade."*
8. *"Cats and dogs seldom get along well together."*
9. *"A joy that’s shared is a joy made double."*
10. *"The birch canoe slid on the smooth dark water."*
11. *"Glue the sheet to the dark blue background."*
12. *"Rice is often served in round white bowls."*
13. *"The box was thrown beside the park path."*
14. *"Four hours of steady work brought quiet success."*
15. *"A large size in shoes is hard to sell."*

### Expressive & Varied Intonations
16. *"Wait, did you really hear that sound?"* (Surprised, rising pitch)
17. *"Look at how smooth this synthesis is becoming."* (Warm, friendly)
18. *"Be quiet for a moment. Listen carefully."* (Soft, hushed)
19. *"I told you we would achieve this result!"* (Confident, excited)
20. *"Whatever happens, we have the complete system under our control."* (Calm, steady)

### Conlang Phonetic Vowel & Glide Exercises
21. *"Ah, eh, ee, oh, oo."* (Sustained clean vowels)
22. *"Mraow, mee-ow, shhh, ksssh."* (Glides and cat/creature bioacoustic sounds)
23. *"La-la-la, ra-ra-ra, tha-tha-tha."* (Liquid and dental consonant transitions)
