/**
 * Utterance Timeline Sequencer Component.
 * Manages Syllables, Phoneme blocks, durations, and creature chips.
 */

class TimelineSequencer {
    constructor(containerId, onStateChanged, onSyllableSelected) {
        this.container = document.getElementById(containerId);
        this.onStateChanged = onStateChanged;
        this.onSyllableSelected = onSyllableSelected;

        this.utterance = [];
        this.activeSyllableIndex = 0;
    }

    setUtterance(utterance) {
        this.utterance = utterance || [];
        if (this.activeSyllableIndex >= this.utterance.length) {
            this.activeSyllableIndex = Math.max(0, this.utterance.length - 1);
        }
        this.render();
    }

    getActiveSyllable() {
        return this.utterance[this.activeSyllableIndex] || null;
    }

    addSyllable() {
        const newSyl = {
            label: "syl",
            prosody: {
                chao_tone: "55",
                phonation: "modal"
            },
            phonemes: [
                { symbol: "s", type: "consonant", duration_ms: 100 },
                { symbol: "a", type: "vowel", duration_ms: 200 }
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
            duration_ms: symbolData.type === "creature" ? 220 : (symbolData.type === "consonant" ? 90 : 180)
        };

        if (p.type === "creature") {
            p.category = symbolData.symbol;
            p.intensity = 0.85;
        }

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

        this.utterance.forEach((syl, sIdx) => {
            const block = document.createElement("div");
            block.className = `syllable-block ${sIdx === this.activeSyllableIndex ? "active" : ""}`;
            
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

            const labelInput = document.createElement("input");
            labelInput.type = "text";
            labelInput.className = "syl-label-input";
            labelInput.value = syl.label || `syl_${sIdx + 1}`;
            labelInput.addEventListener("change", (e) => {
                syl.label = e.target.value;
                this.triggerChange();
            });
            topRow.appendChild(labelInput);

            // Tone Badge
            const toneBadge = document.createElement("span");
            toneBadge.className = "syl-tone-badge";
            toneBadge.textContent = syl.prosody?.chao_tone ? `Tone ${syl.prosody.chao_tone}` : "Custom";
            topRow.appendChild(toneBadge);

            // Delete Syllable Button
            if (this.utterance.length > 1) {
                const delSyl = document.createElement("span");
                delSyl.className = "syl-delete-btn";
                delSyl.innerHTML = "&times;";
                delSyl.title = "Delete Syllable";
                delSyl.addEventListener("click", (e) => this.deleteSyllable(sIdx, e));
                block.appendChild(delSyl);
            }

            block.appendChild(topRow);

            // Phonemes container
            const phonemesCont = document.createElement("div");
            phonemesCont.className = "syl-phonemes-container";

            (syl.phonemes || []).forEach((p, pIdx) => {
                const chip = document.createElement("div");
                let chipClass = "phoneme-chip";
                if (p.type === "creature" || p.symbol.includes("feline") || p.symbol.includes("canine")) {
                    chipClass += " chip-creature";
                } else if (p.symbol.includes("click") || p.symbol.includes("ejective")) {
                    chipClass += " chip-click";
                } else if (p.type === "vowel") {
                    chipClass += " chip-vowel";
                }
                chip.className = chipClass;

                const nameSpan = document.createElement("span");
                nameSpan.className = "chip-name";
                nameSpan.textContent = p.symbol;

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

            block.appendChild(phonemesCont);
            this.container.appendChild(block);
        });
    }
}

window.TimelineSequencer = TimelineSequencer;
