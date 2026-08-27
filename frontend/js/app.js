/**
 * Master Application Controller for Universal Phonetic Speech Studio.
 */

document.addEventListener("DOMContentLoaded", async () => {
    // 1. Core State
    let currentScript = {
        version: "1.0",
        language: "Zha-Kari (Feline Predator Conlang)",
        description: "Predatory feline conlang",
        speaker: {
            name: "Vakkar Shadow-Stalker",
            base_pitch_hz: 135,
            pitch_range_semitones: 14,
            vocal_tract_scale: 0.88,
            breathiness: 0.08,
            vocal_fry: 0.15,
            growl_roughness: 0.40,
            purr_depth: 0.0,
            default_volume_db: 0.0
        },
        utterance: []
    };

    let allSymbols = [];
    let presets = [];

    // 2. Initialize Subcomponents
    const audioSynth = new WebAudioSynth();
    const visualizer = new AudioVisualizer("spectrogramCanvas", "playbackPlayhead");

    let pitchCanvas = null;
    let timeline = null;
    let yamlSync = null;

    // Pitch curve change callback
    const onCurveChanged = (points, activeTone) => {
        const syl = timeline.getActiveSyllable();
        if (syl) {
            syl.prosody.pitch_curve = points;
            syl.prosody.chao_tone = activeTone === "custom" ? null : activeTone;
            timeline.render();
            yamlSync.updateFromState(currentScript);
        }
    };

    // Timeline state change callback
    const onTimelineChanged = (utterance) => {
        currentScript.utterance = utterance;
        yamlSync.updateFromState(currentScript);
    };

    // Syllable selection callback
    const onSyllableSelected = (syl, sIdx) => {
        if (!syl) return;
        document.getElementById("activeSyllableLabel").textContent = `Selected: Syllable ${sIdx + 1} (${syl.label || "syl"})`;
        pitchCanvas.setSyllableProsody(syl.prosody);

        // Update tone button active states
        document.querySelectorAll(".btn-tone").forEach(btn => {
            const tone = btn.getAttribute("data-tone");
            if (syl.prosody.chao_tone === tone) {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        });

        // Update syllable phonation dropdown
        const selPhonation = document.getElementById("selSyllablePhonation");
        if (selPhonation) {
            selPhonation.value = syl.prosody.phonation || "modal";
        }
    };

    // External YAML/JSON edit callback
    const onScriptParsedFromEditor = (parsedScript) => {
        currentScript = parsedScript;
        syncUIToState();
    };

    pitchCanvas = new PitchCanvas("pitchCanvas", onCurveChanged);
    timeline = new TimelineSequencer("syllablesContainer", onTimelineChanged, onSyllableSelected);
    yamlSync = new YamlSync("scriptTextarea", "codeSyncStatus", onScriptParsedFromEditor);

    // 3. UI Synchronization Helper
    function syncUIToState() {
        if (!currentScript.speaker) {
            currentScript.speaker = {
                name: "Default",
                base_pitch_hz: 140,
                pitch_range_semitones: 12,
                vocal_tract_scale: 1.0,
                breathiness: 0.05,
                vocal_fry: 0.0,
                growl_roughness: 0.0,
                purr_depth: 0.0
            };
        }

        const spk = currentScript.speaker;

        // Update Sliders
        document.getElementById("sliderBasePitch").value = spk.base_pitch_hz || 140;
        document.getElementById("valBasePitch").textContent = `${Math.round(spk.base_pitch_hz || 140)} Hz`;

        document.getElementById("sliderPitchRange").value = spk.pitch_range_semitones || 12;
        document.getElementById("valPitchRange").textContent = `${Math.round(spk.pitch_range_semitones || 12)} st`;

        document.getElementById("sliderTractScale").value = spk.vocal_tract_scale || 1.0;
        document.getElementById("valTractScale").textContent = `${(spk.vocal_tract_scale || 1.0).toFixed(2)}x`;

        document.getElementById("sliderBreathiness").value = spk.breathiness || 0.0;
        document.getElementById("valBreathiness").textContent = `${Math.round((spk.breathiness || 0.0) * 100)}%`;

        document.getElementById("sliderVocalFry").value = spk.vocal_fry || 0.0;
        document.getElementById("valVocalFry").textContent = `${Math.round((spk.vocal_fry || 0.0) * 100)}%`;

        document.getElementById("sliderGrowl").value = spk.growl_roughness || 0.0;
        document.getElementById("valGrowl").textContent = `${Math.round((spk.growl_roughness || 0.0) * 100)}%`;

        document.getElementById("sliderPurr").value = spk.purr_depth || 0.0;
        document.getElementById("valPurr").textContent = `${Math.round((spk.purr_depth || 0.0) * 100)}%`;

        document.getElementById("sliderCursiveFlow").value = spk.cursive_flow !== undefined ? spk.cursive_flow : 0.85;
        document.getElementById("valCursiveFlow").textContent = `${Math.round((spk.cursive_flow !== undefined ? spk.cursive_flow : 0.85) * 100)}%`;

        document.getElementById("sliderWarmth").value = spk.acoustic_warmth !== undefined ? spk.acoustic_warmth : 0.40;
        document.getElementById("valWarmth").textContent = `${Math.round((spk.acoustic_warmth !== undefined ? spk.acoustic_warmth : 0.40) * 100)}%`;

        document.getElementById("sliderFleshiness").value = spk.fleshiness !== undefined ? spk.fleshiness : 0.70;
        document.getElementById("valFleshiness").textContent = `${Math.round((spk.fleshiness !== undefined ? spk.fleshiness : 0.70) * 100)}%`;

        document.getElementById("speakerNameBadge").textContent = `Speaker: ${spk.name || "Default"}`;

        pitchCanvas.setSpeaker(spk.base_pitch_hz, spk.pitch_range_semitones);
        timeline.setUtterance(currentScript.utterance);
        pitchCanvas.setSyllableProsody(timeline.getActiveSyllable()?.prosody);
        yamlSync.updateFromState(currentScript);
    }

    // 4. Bind Slider Events
    const bindSlider = (sliderId, labelId, formatFn, spkProp) => {
        const slider = document.getElementById(sliderId);
        slider.addEventListener("input", (e) => {
            const val = parseFloat(e.target.value);
            document.getElementById(labelId).textContent = formatFn(val);
            if (currentScript.speaker) {
                currentScript.speaker[spkProp] = val;
                pitchCanvas.setSpeaker(currentScript.speaker.base_pitch_hz, currentScript.speaker.pitch_range_semitones);
                yamlSync.updateFromState(currentScript);
            }
        });
    };

    bindSlider("sliderBasePitch", "valBasePitch", v => `${Math.round(v)} Hz`, "base_pitch_hz");
    bindSlider("sliderPitchRange", "valPitchRange", v => `${Math.round(v)} st`, "pitch_range_semitones");
    bindSlider("sliderTractScale", "valTractScale", v => `${v.toFixed(2)}x`, "vocal_tract_scale");
    bindSlider("sliderBreathiness", "valBreathiness", v => `${Math.round(v * 100)}%`, "breathiness");
    bindSlider("sliderVocalFry", "valVocalFry", v => `${Math.round(v * 100)}%`, "vocal_fry");
    bindSlider("sliderGrowl", "valGrowl", v => `${Math.round(v * 100)}%`, "growl_roughness");
    bindSlider("sliderPurr", "valPurr", v => `${Math.round(v * 100)}%`, "purr_depth");
    bindSlider("sliderCursiveFlow", "valCursiveFlow", v => `${Math.round(v * 100)}%`, "cursive_flow");
    bindSlider("sliderWarmth", "valWarmth", v => `${Math.round(v * 100)}%`, "acoustic_warmth");
    bindSlider("sliderFleshiness", "valFleshiness", v => `${Math.round(v * 100)}%`, "fleshiness");

    // 5. Bind Tone Preset Buttons
    document.querySelectorAll(".btn-tone").forEach(btn => {
        btn.addEventListener("click", () => {
            const tone = btn.getAttribute("data-tone");
            document.querySelectorAll(".btn-tone").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            pitchCanvas.setChaoTone(tone, true);
        });
    });

    // 6. Bind Syllable Phonation Selector
    document.getElementById("selSyllablePhonation").addEventListener("change", (e) => {
        const syl = timeline.getActiveSyllable();
        if (syl) {
            syl.prosody.phonation = e.target.value;
            yamlSync.updateFromState(currentScript);
        }
    });

    // 7. Bind Timeline Actions
    document.getElementById("btnAddSyllable").addEventListener("click", () => {
        timeline.addSyllable();
    });

    document.getElementById("btnClearUtterance").addEventListener("click", () => {
        if (confirm("Clear all syllables from utterance?")) {
            currentScript.utterance = [];
            timeline.addSyllable();
        }
    });

    // 8. Bind Code Tabs
    document.getElementById("btnTabYaml").addEventListener("click", () => {
        document.getElementById("btnTabYaml").classList.add("active");
        document.getElementById("btnTabJson").classList.remove("active");
        yamlSync.setFormat("yaml");
        yamlSync.updateFromState(currentScript);
    });

    document.getElementById("btnTabJson").addEventListener("click", () => {
        document.getElementById("btnTabJson").classList.add("active");
        document.getElementById("btnTabYaml").classList.remove("active");
        yamlSync.setFormat("json");
        yamlSync.updateFromState(currentScript);
    });

    document.getElementById("btnFormatCode").addEventListener("click", () => {
        yamlSync.updateFromState(currentScript);
    });

    // 9. Load Palette Symbols
    async function loadSymbols() {
        try {
            const res = await fetch("/api/symbols");
            const data = await res.json();
            allSymbols = data.symbols || [];
            renderPaletteChips("all");
        } catch (e) {
            console.error("Failed to load symbols:", e);
        }
    }

    function renderPaletteChips(category, query = "") {
        const container = document.getElementById("paletteChipsContainer");
        container.innerHTML = "";

        const filtered = allSymbols.filter(s => {
            const matchesCat = category === "all" ||
                (category === "vowel" && s.type === "vowel") ||
                (category === "consonant" && s.type === "consonant" && !s.symbol.includes("click") && !s.symbol.includes("ejective")) ||
                (category === "click" && (s.symbol.includes("click") || s.symbol.includes("ejective") || s.symbol.includes("implosive"))) ||
                (category === "creature" && s.type === "creature");

            const matchesQuery = !query || s.symbol.toLowerCase().includes(query) || (s.ipa && s.ipa.toLowerCase().includes(query)) || (s.name && s.name.toLowerCase().includes(query));

            return matchesCat && matchesQuery;
        });

        filtered.forEach(s => {
            const chip = document.createElement("div");
            chip.className = "palette-chip-item";
            chip.title = `${s.name || s.symbol} (IPA: [${s.ipa || s.symbol}]) - Click to add to active syllable`;

            const symSpan = document.createElement("span");
            symSpan.className = "palette-chip-symbol";
            symSpan.textContent = s.symbol;

            const ipaSpan = document.createElement("span");
            ipaSpan.className = "palette-chip-ipa";
            ipaSpan.textContent = `[${s.ipa || s.symbol}]`;

            chip.appendChild(symSpan);
            chip.appendChild(ipaSpan);

            chip.addEventListener("click", () => {
                timeline.addPhonemeToActive(s);
            });

            container.appendChild(chip);
        });
    }

    // Palette tab filter
    document.querySelectorAll(".palette-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".palette-tab").forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            const cat = tab.getAttribute("data-cat");
            const query = document.getElementById("paletteSearch").value.trim().toLowerCase();
            renderPaletteChips(cat, query);
        });
    });

    document.getElementById("paletteSearch").addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        const activeTab = document.querySelector(".palette-tab.active");
        const cat = activeTab ? activeTab.getAttribute("data-cat") : "all";
        renderPaletteChips(cat, query);
    });

    // 10. Load Presets
    async function loadPresets() {
        try {
            const res = await fetch("/api/presets");
            const data = await res.json();
            presets = data.presets || [];

            const select = document.getElementById("presetSelect");
            select.innerHTML = "";

            presets.forEach(p => {
                const opt = document.createElement("option");
                opt.value = p.id;
                opt.textContent = p.name;
                select.appendChild(opt);
            });

            if (presets.length > 0) {
                select.value = presets[0].id;
                currentScript = presets[0].json_data;
                syncUIToState();
            }
        } catch (e) {
            console.error("Failed to load presets:", e);
        }
    }

    document.getElementById("presetSelect").addEventListener("change", (e) => {
        const presetId = e.target.value;
        const p = presets.find(item => item.id === presetId);
        if (p) {
            currentScript = JSON.parse(JSON.stringify(p.json_data));
            syncUIToState();
        }
    });

    // 11. Synthesis & Audio Playback Execution
    async function executeSynthesis() {
        const btn = document.getElementById("btnSynthesize");
        const engineMode = document.getElementById("selectEngineMode")?.value || "neural";
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Synthesizing...`;

        try {
            const res = await fetch("/api/synthesize", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    script_json: currentScript,
                    engine_mode: engineMode
                })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Synthesis failed");
            }

            const data = await res.json();

            // Set to audio player element
            const audioEl = document.getElementById("audioPlayer");
            audioEl.src = data.audio_base64;

            // Play via WebAudio and render spectrogram
            const playRes = await audioSynth.playWavData(data.audio_base64, () => {
                visualizer.stopPlaybackAnimation();
            });

            visualizer.loadAudioBuffer(playRes.buffer);
            visualizer.startPlaybackAnimation(playRes.duration);

            document.getElementById("audioDurationText").textContent = `${playRes.duration.toFixed(2)}s`;

        } catch (err) {
            alert(`Synthesis Error: ${err.message}`);
        } finally {
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-play"></i> Synthesize & Play`;
        }
    }

    document.getElementById("btnSynthesize").addEventListener("click", executeSynthesis);

    document.getElementById("btnStop").addEventListener("click", () => {
        audioSynth.stop();
        visualizer.stopPlaybackAnimation();
        const audioEl = document.getElementById("audioPlayer");
        audioEl.pause();
        audioEl.currentTime = 0;
    });

    // 12. Export Actions
    document.getElementById("btnExportWav").addEventListener("click", async () => {
        const engineMode = document.getElementById("selectEngineMode")?.value || "neural";
        try {
            const res = await fetch("/api/synthesize/wav", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    script_json: currentScript,
                    engine_mode: engineMode
                })
            });
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${(currentScript.language || "conlang").replace(/[^a-z0-9]/gi, "_").toLowerCase()}_speech.wav`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            alert(`Export WAV failed: ${e.message}`);
        }
    });

    document.getElementById("btnExportYaml").addEventListener("click", () => {
        const text = yamlSync.format === "yaml" && window.jsyaml ?
            window.jsyaml.dump(currentScript, { indent: 2 }) :
            JSON.stringify(currentScript, null, 2);

        const blob = new Blob([text], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${(currentScript.language || "conlang").replace(/[^a-z0-9]/gi, "_").toLowerCase()}_script.${yamlSync.format}`;
        a.click();
        URL.revokeObjectURL(url);
    });

    // 13. Reference Modal
    const modal = document.getElementById("referenceModal");
    document.getElementById("btnReferenceModal").addEventListener("click", () => {
        modal.classList.add("open");
    });
    document.getElementById("btnCloseModal").addEventListener("click", () => {
        modal.classList.remove("open");
    });
    modal.addEventListener("click", (e) => {
        if (e.target === modal) modal.classList.remove("open");
    });

    // Initial load
    await loadSymbols();
    await loadPresets();
});
