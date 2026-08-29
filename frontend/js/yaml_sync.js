/**
 * Bi-Directional ExtIPA, YAML, and JSON Synchronization Module.
 */

class YamlSync {
    constructor(textareaId, statusId, onScriptParsed) {
        this.textarea = document.getElementById(textareaId);
        this.statusEl = document.getElementById(statusId);
        this.onScriptParsed = onScriptParsed;

        this.format = "extipa"; // "extipa", "yaml", or "json"
        this.isInternalUpdate = false;

        this.initEvents();
    }

    setFormat(fmt) {
        this.format = fmt;
    }

    initEvents() {
        let debounceTimer = null;
        this.textarea.addEventListener("input", () => {
            if (this.isInternalUpdate) return;
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                this.parseEditorContent();
            }, 250);
        });

        // Bind ExtIPA quick insertion buttons
        document.querySelectorAll(".btn-ipa-insert").forEach(btn => {
            btn.addEventListener("click", () => {
                const ipa = btn.getAttribute("data-ipa");
                if (ipa) {
                    this.insertAtCursor(ipa);
                }
            });
        });
    }

    insertAtCursor(symbol) {
        const el = this.textarea;
        const start = el.selectionStart || 0;
        const end = el.selectionEnd || 0;
        const text = el.value;
        el.value = text.substring(0, start) + symbol + text.substring(end);
        el.selectionStart = el.selectionEnd = start + symbol.length;
        el.focus();
        this.parseEditorContent();
    }

    updateFromState(scriptObj) {
        this.isInternalUpdate = true;
        try {
            if (this.format === "extipa") {
                if (scriptObj.script) {
                    this.textarea.value = typeof scriptObj.script === "string" ? scriptObj.script : scriptObj.script.join(" ");
                } else if (scriptObj.utterance && scriptObj.utterance.length > 0) {
                    const parts = scriptObj.utterance.map(u => {
                        if (u.phrase) return u.phrase;
                        if (u.break || u.break_type) return "ʔ";
                        if (u.label) return u.label;
                        return "";
                    }).filter(Boolean);
                    this.textarea.value = parts.join(" ");
                } else {
                    this.textarea.value = "wiː‿sɔː juː‿ɡoʊ";
                }
            } else if (this.format === "yaml") {
                if (window.jsyaml) {
                    this.textarea.value = window.jsyaml.dump(scriptObj, { indent: 2, lineWidth: -1 });
                } else {
                    this.textarea.value = JSON.stringify(scriptObj, null, 2);
                }
            } else {
                this.textarea.value = JSON.stringify(scriptObj, null, 2);
            }
            this.setStatus(true, "Synchronized");
        } catch (e) {
            console.error("Error formatting script:", e);
        } finally {
            this.isInternalUpdate = false;
        }
    }

    parseEditorContent() {
        const text = this.textarea.value.trim();
        if (!text) return;

        try {
            let data = null;
            if (this.format === "extipa") {
                data = {
                    version: "2.0",
                    language: "ExtIPA Conlang",
                    script: text,
                    speaker: {
                        name: "Speaker",
                        voice_type: "natural_female",
                        base_pitch_hz: 175.0,
                        speed_rate: 1.0
                    }
                };
            } else if (this.format === "yaml" && window.jsyaml) {
                data = window.jsyaml.load(text);
            } else {
                data = JSON.parse(text);
            }

            if (data && typeof data === "object") {
                this.setStatus(true, "Synchronized");
                if (this.onScriptParsed) {
                    this.onScriptParsed(data);
                }
            }
        } catch (err) {
            this.setStatus(false, `Syntax Error: ${err.message}`);
        }
    }

    setStatus(isValid, msg) {
        if (!this.statusEl) return;
        if (isValid) {
            this.statusEl.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${msg}`;
            this.statusEl.style.color = "var(--accent-emerald)";
        } else {
            this.statusEl.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${msg}`;
            this.statusEl.style.color = "var(--accent-rose)";
        }
    }
}

window.YamlSync = YamlSync;
