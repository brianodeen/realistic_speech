/**
 * Bi-Directional YAML and JSON Synchronization Module.
 */

class YamlSync {
    constructor(textareaId, statusId, onScriptParsed) {
        this.textarea = document.getElementById(textareaId);
        this.statusEl = document.getElementById(statusId);
        this.onScriptParsed = onScriptParsed;

        this.format = "yaml"; // "yaml" or "json"
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
            }, 300);
        });
    }

    updateFromState(scriptObj) {
        this.isInternalUpdate = true;
        try {
            if (this.format === "yaml") {
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
            if (this.format === "yaml" && window.jsyaml) {
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
