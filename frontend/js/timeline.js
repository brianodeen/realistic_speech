/**
 * Utterance Timeline Sequencer Component.
 * Supports Extended IPA (ExtIPA) cursive phrases, words, clicks, glottal breaks, and creature bioacoustics.
 */

class TimelineSequencer {
    constructor(containerId, onStateChanged, onSyllableSelected) {
        this.container = document.getElementById(containerId);
        this.onStateChanged = onStateChanged;
        this.onSyllableSelected = onSyllableSelected;

        this.utterance = [];
        this.activeSyllableIndex = 0;
    }

    setScript(scriptObj) {
        if (!scriptObj) {
            this.utterance = [];
            this.render();
            return;
        }

        // Case A: scriptObj has concise script string (e.g. "wiː‿sɔː juː‿ɡoʊ")
        if (scriptObj.script) {
            const scriptText = typeof scriptObj.script === "string" ? scriptObj.script : scriptObj.script.join(" ");
            this.utterance = this.parseExtIPAToSyllables(scriptText);
        }
        // Case B: scriptObj has utterance array
        else if (Array.isArray(scriptObj.utterance) && scriptObj.utterance.length > 0) {
            this.utterance = this.normalizeUtteranceArray(scriptObj.utterance);
        } else {
            this.utterance = this.parseExtIPAToSyllables("wiː‿sɔː juː‿ɡoʊ");
        }

        if (this.activeSyllableIndex >= this.utterance.length) {
            this.activeSyllableIndex = Math.max(0, this.utterance.length - 1);
        }
        this.render();
    }

    setUtterance(utterance) {
        if (Array.isArray(utterance) && utterance.length > 0) {
            this.utterance = this.normalizeUtteranceArray(utterance);
        } else {
            this.utterance = [];
        }
        if (this.activeSyllableIndex >= this.utterance.length) {
            this.activeSyllableIndex = Math.max(0, this.utterance.length - 1);
        }
        this.render();
    }

    normalizeUtteranceArray(rawUtterance) {
        const result = [];
        rawUtterance.forEach((item, idx) => {
            // Glottal stop or pause break
            if (item.break || item.break_type) {
                result.push({
                    id: `break_${idx + 1}`,
                    label: "ʔ",
                    isBreak: true,
                    duration_ms: (item.break === "glottal_stop" || item.break_type === "glottal_stop") ? 45 : 85,
                    prosody: { chao_tone: null, phonation: "glottal_stop" },
                    phonemes: [{ symbol: "ʔ", type: "consonant", name: "Glottal Stop [ʔ]", duration_ms: 45 }]
                });
            }
            // ExtIPA phrase item
            else if (item.phrase) {
                const parsed = this.parseExtIPAToSyllables(item.phrase);
                parsed.forEach(p => {
                    if (item.phonation) p.prosody.phonation = item.phonation;
                    if (item.tone) p.prosody.chao_tone = item.tone;
                    result.push(p);
                });
            }
            // Standard syllable with phonemes
            else if (item.phonemes) {
                result.push(item);
            }
            // Fallback item with label
            else {
                result.push({
                    id: item.id || `syl_${idx + 1}`,
                    label: item.label || `syl_${idx + 1}`,
                    duration_ms: item.duration_ms || 200,
                    prosody: item.prosody || { chao_tone: null, phonation: "modal" },
                    phonemes: item.phonemes || [{ symbol: item.label || "a", type: "vowel", duration_ms: 180 }]
                });
            }
        });
        return result;
    }

    parseExtIPAToSyllables(scriptText) {
        if (!scriptText || typeof scriptText !== "string") return [];
        // Isolate glottal break characters (ʔ, |, ‖) with spaces so they become distinct tokens
        const preprocessed = scriptText.replace(/([ʔ|‖])/g, " $1 ");
        const tokens = preprocessed.trim().split(/\s+/);
        const syllables = [];

        tokens.forEach((tok, idx) => {
            tok = tok.trim();
            if (!tok) return;

            // Glottal Stop or Boundary Pen-Lift
            if (tok === "ʔ" || tok === "|" || tok === "‖") {
                syllables.push({
                    id: `break_${idx + 1}`,
                    label: "ʔ",
                    isBreak: true,
                    duration_ms: tok === "ʔ" ? 45 : 90,
                    prosody: { chao_tone: null, phonation: "glottal_stop" },
                    phonemes: [{ symbol: "ʔ", type: "consonant", name: "Glottal Stop [ʔ]", duration_ms: 45 }]
                });
                return;
            }

            // Detect creature phonation
            let phonation = "modal";
            if (tok.includes("ʭ")) phonation = "ventricular_growl";
            else if (tok.includes("ʬ̃") || tok.includes("ʙ")) phonation = "feline_purr";
            else if (tok.includes("f͌") || tok.includes("v͌")) phonation = "snarl";
            else if (tok.includes("ạ")) phonation = "breathy";
            else if (tok.includes("a̰")) phonation = "creaky";

            // Extract IPA phonemes from token
            const phonemes = this.extractPhonemesFromToken(tok);

            syllables.push({
                id: `syl_${idx + 1}`,
                label: tok,
                duration_ms: phonemes.reduce((sum, p) => sum + (p.duration_ms || 100), 0) || 220,
                prosody: { chao_tone: null, phonation: phonation },
                phonemes: phonemes
            });
        });

        return syllables;
    }

    extractPhonemesFromToken(tok) {
        const ipaTable = [
            // Clicks & Ejectives (African & Conlang)
            { sym: "kǀ", type: "click", name: "Dental Click [kǀ]" },
            { sym: "kǃ", type: "click", name: "Alveolar Click [kǃ]" },
            { sym: "kǁ", type: "click", name: "Lateral Click [kǁ]" },
            { sym: "kʘ", type: "click", name: "Bilabial Click [kʘ]" },
            { sym: "ɡǀ", type: "click", name: "Voiced Dental Click [ɡǀ]" },
            { sym: "ɡǃ", type: "click", name: "Voiced Alveolar Click [ɡǃ]" },
            { sym: "ɡǁ", type: "click", name: "Voiced Lateral Click [ɡǁ]" },
            { sym: "ŋǀ", type: "click", name: "Nasal Dental Click [ŋǀ]" },
            { sym: "ŋǃ", type: "click", name: "Nasal Alveolar Click [ŋǃ]" },
            { sym: "ŋǁ", type: "click", name: "Nasal Lateral Click [ŋǁ]" },
            { sym: "ǀ", type: "click", name: "Dental Click [ǀ]" },
            { sym: "ǃ", type: "click", name: "Alveolar Click [ǃ]" },
            { sym: "ǁ", type: "click", name: "Lateral Click [ǁ]" },
            { sym: "ʘ", type: "click", name: "Bilabial Click [ʘ]" },
            { sym: "ǂ", type: "click", name: "Palatoalveolar Click [ǂ]" },
            { sym: "kʼ", type: "click", name: "Velar Ejective [kʼ]" },
            { sym: "tʼ", type: "click", name: "Alveolar Ejective [tʼ]" },
            { sym: "pʼ", type: "click", name: "Bilabial Ejective [pʼ]" },
            { sym: "sʼ", type: "click", name: "Ejective [sʼ]" },

            // Cursive Ties, Ligatures & Clusters
            { sym: "‿", type: "tie", name: "Cursive Flow Tie [‿]" },
            { sym: "͡", type: "tie", name: "Ligature Tie [͡]" },
            { sym: "t͡s", type: "consonant", name: "Affricate [t͡s]" },
            { sym: "t͡ʃ", type: "consonant", name: "Affricate [t͡ʃ]" },
            { sym: "d͡ʒ", type: "consonant", name: "Affricate [d͡ʒ]" },
            { sym: "k͡r", type: "consonant", name: "Cluster [k͡r]" },

            // Creature bioacoustics
            { sym: "ʭ", type: "creature", name: "Ventricular Growl [ʭ]" },
            { sym: "ʬ̃", type: "creature", name: "Feline Purr Trill [ʬ̃]" },
            { sym: "f͌", type: "creature", name: "Velopharyngeal Snarl [f͌]" },
            { sym: "v͌", type: "creature", name: "Velopharyngeal Snarl [v͌]" },
            { sym: "ʢ", type: "creature", name: "Epiglottal Growl [ʢ]" },
            { sym: "ʡ", type: "creature", name: "Epiglottal Stop [ʡ]" },

            // Howl & Vowel Sustains
            { sym: "awoooo", type: "vowel", name: "Howl Glide [awoooo]" },
            { sym: "oooo", type: "vowel", name: "Long Howl [oooo]" },
            { sym: "ooo", type: "vowel", name: "Sustained [ooo]" },

            // Long Vowels & Diphthongs
            { sym: "iː", type: "vowel", name: "Long [iː]" },
            { sym: "uː", type: "vowel", name: "Long [uː]" },
            { sym: "aː", type: "vowel", name: "Long [aː]" },
            { sym: "oː", type: "vowel", name: "Long [oː]" },
            { sym: "eː", type: "vowel", name: "Long [eː]" },
            { sym: "ɔː", type: "vowel", name: "Long [ɔː]" },
            { sym: "əː", type: "vowel", name: "Long [əː]" },
            { sym: "oʊ", type: "vowel", name: "Diphthong [oʊ]" },
            { sym: "aɪ", type: "vowel", name: "Diphthong [aɪ]" },
            { sym: "eɪ", type: "vowel", name: "Diphthong [eɪ]" },
            { sym: "aʊ", type: "vowel", name: "Diphthong [aʊ]" },
            { sym: "ɔɪ", type: "vowel", name: "Diphthong [ɔɪ]" },

            // Guttural & Pharyngeal
            { sym: "ħ", type: "consonant", name: "Voiceless Pharyngeal [ħ]" },
            { sym: "ʕ", type: "consonant", name: "Voiced Pharyngeal [ʕ]" },
            { sym: "q", type: "consonant", name: "Uvular Stop [q]" },
            { sym: "χ", type: "consonant", name: "Voiceless Uvular [χ]" },
            { sym: "ʁ", type: "consonant", name: "Voiced Uvular [ʁ]" },
            { sym: "ɡˠ", type: "consonant", name: "Velarized [ɡˠ]" },
            { sym: "rˠ", type: "consonant", name: "Velarized Trill [rˠ]" },
            { sym: "ˠ", type: "consonant", name: "Velarized [ˠ]" },
            { sym: "ʔ", type: "consonant", name: "Glottal [ʔ]" },
            { sym: "ˀ", type: "click", name: "Glottalized [ˀ]" },

            // Standard Consonants
            { sym: "ʃ", type: "consonant", name: "Fricative [ʃ]" },
            { sym: "ʒ", type: "consonant", name: "Fricative [ʒ]" },
            { sym: "θ", type: "consonant", name: "Dental [θ]" },
            { sym: "ð", type: "consonant", name: "Dental [ð]" },
            { sym: "ŋ", type: "consonant", name: "Nasal [ŋ]" },
            { sym: "ɲ", type: "consonant", name: "Nasal [ɲ]" },
            { sym: "ɣ", type: "consonant", name: "Fricative [ɣ]" },
            { sym: "x", type: "consonant", name: "Fricative [x]" },
            { sym: "ʙ", type: "consonant", name: "Trill [ʙ]" },
            { sym: "r", type: "consonant", name: "Trill [r]" },
            { sym: "w", type: "consonant", name: "Glide [w]" },
            { sym: "j", type: "consonant", name: "Glide [j]" },
            { sym: "k", type: "consonant", name: "Stop [k]" },
            { sym: "ɡ", type: "consonant", name: "Stop [ɡ]" },
            { sym: "g", type: "consonant", name: "Stop [g]" },
            { sym: "p", type: "consonant", name: "Stop [p]" },
            { sym: "b", type: "consonant", name: "Stop [b]" },
            { sym: "t", type: "consonant", name: "Stop [t]" },
            { sym: "d", type: "consonant", name: "Stop [d]" },
            { sym: "m", type: "consonant", name: "Nasal [m]" },
            { sym: "n", type: "consonant", name: "Nasal [n]" },
            { sym: "s", type: "consonant", name: "Fricative [s]" },
            { sym: "z", type: "consonant", name: "Fricative [z]" },
            { sym: "l", type: "consonant", name: "Lateral [l]" },
            { sym: "h", type: "consonant", name: "Aspirate [h]" },
            { sym: "f", type: "consonant", name: "Fricative [f]" },
            { sym: "v", type: "consonant", name: "Fricative [v]" },

            // Standard Vowels
            { sym: "i", type: "vowel", name: "Close Front [i]" },
            { sym: "u", type: "vowel", name: "Close Back [u]" },
            { sym: "a", type: "vowel", name: "Open Front [a]" },
            { sym: "o", type: "vowel", name: "Close-Mid [o]" },
            { sym: "e", type: "vowel", name: "Close-Mid [e]" },
            { sym: "ə", type: "vowel", name: "Schwa [ə]" },
            { sym: "ɛ", type: "vowel", name: "Open-Mid [ɛ]" },
            { sym: "æ", type: "vowel", name: "Near-Open [æ]" },
            { sym: "ʌ", type: "vowel", name: "Wedge [ʌ]" },
            { sym: "ɔ", type: "vowel", name: "Open-Mid [ɔ]" },
            { sym: "ɨ", type: "vowel", name: "Close Central [ɨ]" },
            { sym: "ɯ", type: "vowel", name: "Close Back [ɯ]" },
            { sym: "ː", type: "tie", name: "Length [ː]" },

            // Mandarin Tonal Vowels
            { sym: "ā", type: "vowel", name: "Tone 1 [ā]" },
            { sym: "á", type: "vowel", name: "Tone 2 [á]" },
            { sym: "ǎ", type: "vowel", name: "Tone 3 [ǎ]" },
            { sym: "à", type: "vowel", name: "Tone 4 [à]" },
            { sym: "ē", type: "vowel", name: "Tone 1 [ē]" },
            { sym: "é", type: "vowel", name: "Tone 2 [é]" },
            { sym: "ě", type: "vowel", name: "Tone 3 [ě]" },
            { sym: "è", type: "vowel", name: "Tone 4 [è]" },
            { sym: "ī", type: "vowel", name: "Tone 1 [ī]" },
            { sym: "í", type: "vowel", name: "Tone 2 [í]" },
            { sym: "ǐ", type: "vowel", name: "Tone 3 [ǐ]" },
            { sym: "ì", type: "vowel", name: "Tone 4 [ì]" },
            { sym: "ō", type: "vowel", name: "Tone 1 [ō]" },
            { sym: "ó", type: "vowel", name: "Tone 2 [ó]" },
            { sym: "ǒ", type: "vowel", name: "Tone 3 [ǒ]" },
            { sym: "ò", type: "vowel", name: "Tone 4 [ò]" },
            { sym: "ū", type: "vowel", name: "Tone 1 [ū]" },
            { sym: "ú", type: "vowel", name: "Tone 2 [ú]" },
            { sym: "ǔ", type: "vowel", name: "Tone 3 [ǔ]" },
            { sym: "ù", type: "vowel", name: "Tone 4 [ù]" },
        ];

        const phonemes = [];
        let i = 0;
        while (i < tok.length) {
            let matched = false;
            for (const item of ipaTable) {
                if (tok.startsWith(item.sym, i)) {
                    phonemes.push({
                        symbol: item.sym,
                        type: item.type,
                        name: item.name,
                        duration_ms: item.type === "vowel" ? 180 : (item.type === "tie" ? 60 : (item.type === "creature" ? 220 : 100))
                    });
                    i += item.sym.length;
                    matched = true;
                    break;
                }
            }
            if (!matched) {
                const char = tok[i];
                // Support any Unicode letter or combining mark
                if (/\p{L}|\p{M}/u.test(char)) {
                    const isVowel = /[aeiouyāáǎàēéěèīíǐìōóǒòūúǔùɨʉɯɪʏʊøɘɵɤœɜɞʌɔæɐɑɒ]/i.test(char);
                    phonemes.push({
                        symbol: char,
                        type: isVowel ? "vowel" : "consonant",
                        name: `[${char}]`,
                        duration_ms: isVowel ? 160 : 110
                    });
                }
                i++;
            }
        }
        return phonemes.length > 0 ? phonemes : [{ symbol: tok, type: "vowel", name: `[${tok}]`, duration_ms: 200 }];
    }

    getActiveSyllable() {
        return this.utterance[this.activeSyllableIndex] || null;
    }

    addSyllable() {
        const newSyl = {
            id: `syl_${this.utterance.length + 1}`,
            label: "wiː‿sɔː",
            prosody: {
                chao_tone: "55",
                phonation: "modal"
            },
            phonemes: [
                { symbol: "w", type: "consonant", name: "[w]", duration_ms: 90 },
                { symbol: "iː", type: "vowel", name: "Long [iː]", duration_ms: 180 },
                { symbol: "‿", type: "tie", name: "Cursive Tie [‿]", duration_ms: 60 },
                { symbol: "s", type: "consonant", name: "[s]", duration_ms: 90 },
                { symbol: "ɔː", type: "vowel", name: "Long [ɔː]", duration_ms: 180 }
            ]
        };
        this.utterance.push(newSyl);
        this.activeSyllableIndex = this.utterance.length - 1;
        this.render();
        this.triggerChange();
    }

    deleteSyllable(idx, e) {
        if (e) e.stopPropagation();
        if (this.utterance.length <= 1) return;
        this.utterance.splice(idx, 1);
        if (this.activeSyllableIndex >= this.utterance.length) {
            this.activeSyllableIndex = this.utterance.length - 1;
        }
        this.render();
        this.triggerChange();
    }

    addPhonemeToActive(symbolData) {
        const syl = this.getActiveSyllable();
        if (!syl) return;

        const p = {
            symbol: symbolData.symbol,
            type: symbolData.type || (symbolData.category === "creature" ? "creature" : "vowel"),
            name: symbolData.ipa ? `[${symbolData.ipa}]` : symbolData.symbol,
            duration_ms: symbolData.type === "creature" ? 220 : (symbolData.type === "consonant" ? 90 : 180)
        };

        if (p.type === "creature") {
            p.category = symbolData.symbol;
            p.intensity = 0.85;
        }

        syl.phonemes = syl.phonemes || [];
        syl.phonemes.push(p);
        this.render();
        this.triggerChange();
    }

    deletePhoneme(sylIdx, pIdx, e) {
        if (e) e.stopPropagation();
        if (this.utterance[sylIdx] && this.utterance[sylIdx].phonemes) {
            this.utterance[sylIdx].phonemes.splice(pIdx, 1);
            this.render();
            this.triggerChange();
        }
    }

    triggerChange() {
        if (this.onStateChanged) {
            this.onStateChanged(this.utterance);
        }
        if (this.onSyllableSelected) {
            this.onSyllableSelected(this.getActiveSyllable(), this.activeSyllableIndex);
        }
    }

    render() {
        this.container.innerHTML = "";

        if (this.utterance.length === 0) {
            this.container.innerHTML = `<div style="color: var(--text-dim); padding: 18px; font-size: 0.85rem; display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-circle-info"></i> No syllables loaded. Click <strong>Add Syllable</strong> or select a preset above.
            </div>`;
            return;
        }

        this.utterance.forEach((syl, sIdx) => {
            const block = document.createElement("div");
            const isBreak = syl.isBreak || syl.label === "ʔ" || syl.prosody?.phonation === "glottal_stop";
            block.className = `syllable-block ${sIdx === this.activeSyllableIndex ? "active" : ""} ${isBreak ? "syllable-break" : ""}`;

            block.addEventListener("click", () => {
                this.activeSyllableIndex = sIdx;
                this.render();
                if (this.onSyllableSelected) {
                    this.onSyllableSelected(syl, sIdx);
                }
            });

            // Top Row
            const topRow = document.createElement("div");
            topRow.className = "syllable-top-row";

            if (isBreak) {
                const leftWrap = document.createElement("div");
                leftWrap.style.cssText = "display: flex; align-items: center; gap: 6px;";
                const numPill = document.createElement("span");
                numPill.className = "syl-num-pill";
                numPill.textContent = `#${sIdx + 1}`;
                const breakBadge = document.createElement("span");
                breakBadge.className = "badge";
                breakBadge.style.cssText = "background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4); font-weight: 700;";
                breakBadge.textContent = "ʔ Glottal Pen-Lift";
                leftWrap.appendChild(numPill);
                leftWrap.appendChild(breakBadge);
                topRow.appendChild(leftWrap);
            } else {
                const leftWrap = document.createElement("div");
                leftWrap.style.cssText = "display: flex; align-items: center; gap: 6px; flex: 1; min-width: 0;";
                const numPill = document.createElement("span");
                numPill.className = "syl-num-pill";
                numPill.textContent = `#${sIdx + 1}`;

                const labelInput = document.createElement("input");
                labelInput.type = "text";
                labelInput.className = "syl-label-input";
                labelInput.value = syl.label || `syl_${sIdx + 1}`;
                labelInput.title = "ExtIPA Syllable/Word (Editable)";
                labelInput.addEventListener("change", (e) => {
                    syl.label = e.target.value;
                    syl.phonemes = this.extractPhonemesFromToken(e.target.value);
                    syl.duration_ms = syl.phonemes.reduce((sum, p) => sum + (p.duration_ms || 100), 0);
                    this.triggerChange();
                    this.render();
                });
                leftWrap.appendChild(numPill);
                leftWrap.appendChild(labelInput);
                topRow.appendChild(leftWrap);

                // Tone or Phonation Badge
                if (syl.prosody?.phonation && syl.prosody.phonation !== "modal") {
                    const phBadge = document.createElement("span");
                    phBadge.className = "badge";
                    phBadge.style.cssText = "background: rgba(245, 158, 11, 0.2); color: #f59e0b;";
                    phBadge.textContent = syl.prosody.phonation;
                    topRow.appendChild(phBadge);
                } else if (syl.prosody?.chao_tone) {
                    const toneBadge = document.createElement("span");
                    toneBadge.className = "syl-tone-badge";
                    toneBadge.textContent = `Tone ${syl.prosody.chao_tone}`;
                    topRow.appendChild(toneBadge);
                }
            }

            // Delete Button
            if (this.utterance.length > 1) {
                const delSyl = document.createElement("span");
                delSyl.className = "syl-delete-btn";
                delSyl.innerHTML = "&times;";
                delSyl.title = "Delete Syllable";
                delSyl.addEventListener("click", (e) => this.deleteSyllable(sIdx, e));
                topRow.appendChild(delSyl);
            }

            block.appendChild(topRow);

            // Phonemes container
            const phonemesCont = document.createElement("div");
            phonemesCont.className = "syl-phonemes-container";

            if (isBreak) {
                const breakInfo = document.createElement("div");
                breakInfo.className = "break-card-content";
                breakInfo.innerHTML = `
                    <div style="color: #f59e0b; font-size: 0.78rem; font-weight: 600; text-align: center; padding: 6px 0;">
                        <i class="fa-solid fa-hand-dots"></i> Glottal Stop / Pause
                    </div>
                    <div style="color: var(--text-dim); font-size: 0.68rem; text-align: center;">
                        ${Math.round(syl.duration_ms || 45)}ms pen-lift break
                    </div>
                `;
                phonemesCont.appendChild(breakInfo);
            } else {
                (syl.phonemes || []).forEach((p, pIdx) => {
                    const chip = document.createElement("div");
                    let chipClass = "phoneme-chip";
                    if (p.type === "creature" || (p.symbol && (p.symbol.includes("feline") || p.symbol.includes("canine") || p.symbol === "ʭ" || p.symbol === "ʬ̃" || p.symbol === "f͌" || p.symbol === "v͌"))) {
                        chipClass += " chip-creature";
                    } else if (p.type === "click" || (p.symbol && (p.symbol.includes("click") || p.symbol.includes("ejective") || p.symbol.includes("ǀ") || p.symbol.includes("ǃ") || p.symbol.includes("ǁ") || p.symbol.includes("ʘ") || p.symbol.includes("ǂ") || p.symbol.includes("ʼ")))) {
                        chipClass += " chip-click";
                    } else if (p.type === "tie" || p.symbol === "‿" || p.symbol === "͡") {
                        chipClass += " chip-tie";
                    } else if (p.type === "vowel") {
                        chipClass += " chip-vowel";
                    }
                    chip.className = chipClass;

                    const nameSpan = document.createElement("span");
                    nameSpan.className = "chip-name";
                    nameSpan.textContent = p.name || p.symbol;

                    const durSpan = document.createElement("span");
                    durSpan.className = "chip-dur";
                    durSpan.textContent = `${Math.round(p.duration_ms || 100)}ms`;

                    const delBtn = document.createElement("span");
                    delBtn.className = "chip-delete";
                    delBtn.innerHTML = "&times;";
                    delBtn.title = "Remove Phoneme";
                    delBtn.addEventListener("click", (e) => this.deletePhoneme(sIdx, pIdx, e));

                    chip.appendChild(nameSpan);
                    chip.appendChild(durSpan);
                    chip.appendChild(delBtn);
                    phonemesCont.appendChild(chip);
                });
            }

            block.appendChild(phonemesCont);

            // Card Footer
            if (!isBreak) {
                const cardFooter = document.createElement("div");
                cardFooter.style.cssText = "display: flex; justify-content: space-between; align-items: center; font-size: 0.68rem; color: var(--text-dim); margin-top: 4px; padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.05);";
                cardFooter.innerHTML = `<span>Duration:</span><strong style="color: var(--text-main);">${Math.round(syl.duration_ms || 180)}ms</strong>`;
                block.appendChild(cardFooter);
            }

            this.container.appendChild(block);
        });
    }
}

window.TimelineSequencer = TimelineSequencer;
