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
        timeline.setScript(currentScript);
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

    // 8. Bind Code Tabs (ExtIPA, YAML, JSON)
    const tabExtIpa = document.getElementById("btnTabExtIpa");
    const tabYaml = document.getElementById("btnTabYaml");
    const tabJson = document.getElementById("btnTabJson");

    if (tabExtIpa) {
        tabExtIpa.addEventListener("click", () => {
            tabExtIpa.classList.add("active");
            if (tabYaml) tabYaml.classList.remove("active");
            if (tabJson) tabJson.classList.remove("active");
            yamlSync.setFormat("extipa");
            yamlSync.updateFromState(currentScript);
        });
    }

    if (tabYaml) {
        tabYaml.addEventListener("click", () => {
            tabYaml.classList.add("active");
            if (tabExtIpa) tabExtIpa.classList.remove("active");
            if (tabJson) tabJson.classList.remove("active");
            yamlSync.setFormat("yaml");
            yamlSync.updateFromState(currentScript);
        });
    }

    if (tabJson) {
        tabJson.addEventListener("click", () => {
            tabJson.classList.add("active");
            if (tabExtIpa) tabExtIpa.classList.remove("active");
            if (tabYaml) tabYaml.classList.remove("active");
            yamlSync.setFormat("json");
            yamlSync.updateFromState(currentScript);
        });
    }

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
                const mode = document.getElementById("selectEngineMode")?.value || "neural";
                updateEvalContext(presets[0], mode, currentScript);
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
            const mode = document.getElementById("selectEngineMode")?.value || "neural";
            updateEvalContext(p, mode, currentScript);
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

            // Update evaluation context with current synthesis parameters
            const presetId = document.getElementById("presetSelect")?.value;
            const activePreset = presets.find(item => item.id === presetId);
            updateEvalContext(activePreset, engineMode, currentScript);

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

    // ==========================================================================
    // 14. 1-10 Evaluation & ElevenLabs-Parity Quality Benchmark System (Per-Preset)
    // ==========================================================================
    const presetFeedbackStore = {};
    let activeFeedbackPresetId = "custom";

    function getCleanPresetScores() {
        return {
            smoothness: 8,
            realism: 8,
            pronunciation: 9,
            prosody: 8,
            bioacoustics: null, // null for N/A
            cleanliness: 9,
            elevenlabs_parity: 8,
        };
    }

    const evalState = {
        scores: getCleanPresetScores(),
        tags: new Set(),
        lastSynthesisInfo: {
            preset_id: "custom",
            preset_name: "Custom Script",
            language: "Conlang",
            engine_mode: "neural",
            script_text: "",
        },
    };

    function syncCurrentPresetFeedbackToStore() {
        if (!activeFeedbackPresetId) return;
        const notes = document.getElementById("evalNotesTextarea")?.value || "";
        presetFeedbackStore[activeFeedbackPresetId] = {
            scores: { ...evalState.scores },
            tags: new Set(evalState.tags),
            notes: notes,
            preset_name: evalState.lastSynthesisInfo.preset_name,
            language: evalState.lastSynthesisInfo.language,
        };
    }

    function applyScoresToUI(scores) {
        evalState.scores = { ...scores };
        const metrics = [
            { id: "smoothness", badgeId: "valSmoothness" },
            { id: "realism", badgeId: "valRealism" },
            { id: "pronunciation", badgeId: "valPronunciation" },
            { id: "prosody", badgeId: "valProsody" },
            { id: "bioacoustics", badgeId: "valBioacoustics" },
            { id: "cleanliness", badgeId: "valCleanliness" },
            { id: "elevenlabs_parity", badgeId: "valParity" },
        ];

        metrics.forEach(m => {
            const container = document.querySelector(`.pill-rating-group[data-metric="${m.id}"]`);
            if (!container) return;
            const val = scores[m.id];

            container.querySelectorAll(".pill-btn").forEach(b => b.classList.remove("active"));
            if (val === null || val === undefined) {
                const naBtn = container.querySelector(".pill-na");
                if (naBtn) naBtn.classList.add("active");
                const badge = document.getElementById(m.badgeId);
                if (badge) badge.textContent = "N/A";
            } else {
                const btn = container.querySelector(`.pill-btn[data-score="${val}"]`);
                if (btn) btn.classList.add("active");
                const badge = document.getElementById(m.badgeId);
                if (badge) badge.textContent = `${val}/10`;
            }
        });
    }

    function applyTagsToUI(tagSet) {
        evalState.tags = new Set(tagSet || []);
        document.querySelectorAll(".eval-tag-chip").forEach(chip => {
            const tag = chip.getAttribute("data-tag");
            if (evalState.tags.has(tag)) {
                chip.classList.add("selected");
            } else {
                chip.classList.remove("selected");
            }
        });
    }

    function loadPresetFeedback(presetId, presetName) {
        activeFeedbackPresetId = presetId || "custom";
        const saved = presetFeedbackStore[presetId];

        if (saved) {
            applyScoresToUI(saved.scores || getCleanPresetScores());
            applyTagsToUI(saved.tags || []);
            const notesEl = document.getElementById("evalNotesTextarea");
            if (notesEl) notesEl.value = saved.notes || "";
            setEvalBadge(`${presetName || presetId} [Saved Feedback]`);
        } else {
            applyScoresToUI(getCleanPresetScores());
            applyTagsToUI([]);
            const notesEl = document.getElementById("evalNotesTextarea");
            if (notesEl) notesEl.value = "";
            setEvalBadge(`${presetName || presetId} [Not Yet Rated]`);
            syncCurrentPresetFeedbackToStore();
        }
    }

    function setEvalBadge(text) {
        const badge = document.getElementById("evalContextBadge");
        if (badge) badge.textContent = text;
    }

    function updateEvalContext(presetObj, engineMode, scriptObj) {
        const presetId = presetObj ? presetObj.id : "custom";
        const presetName = presetObj ? presetObj.name : (currentScript.language || "Custom Script");
        evalState.lastSynthesisInfo.preset_id = presetId;
        evalState.lastSynthesisInfo.preset_name = presetName;
        evalState.lastSynthesisInfo.language = presetObj ? (presetObj.language || presetObj.name) : (currentScript.language || "Conlang");
        evalState.lastSynthesisInfo.engine_mode = engineMode;

        if (scriptObj.script) {
            evalState.lastSynthesisInfo.script_text = typeof scriptObj.script === "string" ? scriptObj.script : scriptObj.script.join(" ");
        } else {
            evalState.lastSynthesisInfo.script_text = JSON.stringify(scriptObj.utterance || []);
        }

        loadPresetFeedback(presetId, presetName);
    }

    // Initialize 1-10 Pill Rating Groups
    function initRatingPills() {
        const metrics = [
            { id: "smoothness", defaultVal: 8, hasNA: false, badgeId: "valSmoothness" },
            { id: "realism", defaultVal: 8, hasNA: false, badgeId: "valRealism" },
            { id: "pronunciation", defaultVal: 9, hasNA: false, badgeId: "valPronunciation" },
            { id: "prosody", defaultVal: 8, hasNA: false, badgeId: "valProsody" },
            { id: "bioacoustics", defaultVal: null, hasNA: true, badgeId: "valBioacoustics" },
            { id: "cleanliness", defaultVal: 9, hasNA: false, badgeId: "valCleanliness" },
            { id: "elevenlabs_parity", defaultVal: 8, hasNA: false, badgeId: "valParity" },
        ];

        metrics.forEach(m => {
            const container = document.querySelector(`.pill-rating-group[data-metric="${m.id}"]`);
            if (!container) return;
            container.innerHTML = "";

            if (m.hasNA) {
                const naBtn = document.createElement("button");
                naBtn.type = "button";
                naBtn.className = `pill-btn pill-na ${m.defaultVal === null ? "active" : ""}`;
                naBtn.textContent = "N/A";
                naBtn.title = "Not applicable for human-only scripts";
                naBtn.addEventListener("click", () => {
                    evalState.scores[m.id] = null;
                    container.querySelectorAll(".pill-btn").forEach(b => b.classList.remove("active"));
                    naBtn.classList.add("active");
                    const badge = document.getElementById(m.badgeId);
                    if (badge) badge.textContent = "N/A";
                    syncCurrentPresetFeedbackToStore();
                });
                container.appendChild(naBtn);
            }

            for (let i = 1; i <= 10; i++) {
                const btn = document.createElement("button");
                btn.type = "button";
                btn.className = `pill-btn ${m.defaultVal === i ? "active" : ""}`;
                btn.setAttribute("data-score", i);
                btn.textContent = i;
                btn.title = `Score: ${i}/10`;
                btn.addEventListener("click", () => {
                    evalState.scores[m.id] = i;
                    container.querySelectorAll(".pill-btn").forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    const badge = document.getElementById(m.badgeId);
                    if (badge) badge.textContent = `${i}/10`;
                    syncCurrentPresetFeedbackToStore();
                });
                container.appendChild(btn);
            }

            const badge = document.getElementById(m.badgeId);
            if (badge) {
                badge.textContent = m.defaultVal === null ? "N/A" : `${m.defaultVal}/10`;
            }
        });
    }

    // Diagnostic Issue Tag Toggles
    document.querySelectorAll(".eval-tag-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const tag = chip.getAttribute("data-tag");
            if (chip.classList.contains("selected")) {
                chip.classList.remove("selected");
                evalState.tags.delete(tag);
            } else {
                chip.classList.add("selected");
                evalState.tags.add(tag);
            }
            syncCurrentPresetFeedbackToStore();
        });
    });

    // Notes live sync to per-preset store
    document.getElementById("evalNotesTextarea")?.addEventListener("input", () => {
        syncCurrentPresetFeedbackToStore();
    });

    // Load initial feedback from API to populate per-preset store
    async function populateFeedbackStoreFromBackend() {
        try {
            const res = await fetch("/api/feedback");
            if (!res.ok) return;
            const data = await res.json();
            const list = data.evaluations || [];
            // Evaluations are newest first
            list.forEach(r => {
                if (r.preset_id && !presetFeedbackStore[r.preset_id]) {
                    presetFeedbackStore[r.preset_id] = {
                        scores: r.scores || getCleanPresetScores(),
                        tags: new Set(r.tags || []),
                        notes: r.notes || "",
                        preset_name: r.preset_name,
                        language: r.language,
                    };
                }
            });
        } catch (e) {
            console.warn("Could not pre-populate feedback store:", e);
        }
    }

    // Submit Evaluation Handler
    async function submitEvaluation() {
        const btn = document.getElementById("btnSubmitEvaluation");
        const statusEl = document.getElementById("evalSubmitStatus");
        const notes = document.getElementById("evalNotesTextarea").value.trim();

        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Submitting...`;
        statusEl.textContent = "";

        syncCurrentPresetFeedbackToStore();

        const payload = {
            preset_id: evalState.lastSynthesisInfo.preset_id,
            preset_name: evalState.lastSynthesisInfo.preset_name,
            language: evalState.lastSynthesisInfo.language,
            engine_mode: evalState.lastSynthesisInfo.engine_mode,
            script_text: evalState.lastSynthesisInfo.script_text || "",
            scores: evalState.scores,
            tags: Array.from(evalState.tags),
            notes: notes,
            speaker_params: currentScript.speaker || {},
        };

        try {
            const res = await fetch("/api/feedback", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Submission failed");
            }

            statusEl.className = "eval-status-message success";
            statusEl.textContent = "✓ Evaluation saved successfully for this preset!";
            setEvalBadge(`${evalState.lastSynthesisInfo.preset_name} [Feedback Saved ✓]`);

            await updateEvaluationCounters();

            setTimeout(() => {
                statusEl.textContent = "";
            }, 4000);
        } catch (err) {
            statusEl.className = "eval-status-message error";
            statusEl.textContent = `Error: ${err.message}`;
        } finally {
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Submit Evaluation & Feedback`;
        }
    }

    document.getElementById("btnSubmitEvaluation").addEventListener("click", submitEvaluation);

    // Ctrl+Enter to submit notes
    document.getElementById("evalNotesTextarea").addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            submitEvaluation();
        }
    });

    // Update Evaluation Counters in UI
    async function updateEvaluationCounters() {
        try {
            const res = await fetch("/api/feedback/summary");
            if (!res.ok) return;
            const data = await res.json();
            const summary = data.summary || {};
            const total = summary.total_evaluations || 0;

            const badge1 = document.getElementById("evalCountBadge");
            const badge2 = document.getElementById("evalHistoryCountText");
            if (badge1) badge1.textContent = total;
            if (badge2) badge2.textContent = total;
        } catch (e) {
            console.warn("Could not fetch feedback summary:", e);
        }
    }

    // ==========================================================================
    // 15. Evaluation History & Benchmark Trends Modal
    // ==========================================================================
    const historyModal = document.getElementById("evalHistoryModal");

    async function openHistoryModal() {
        historyModal.classList.add("open");
        await loadAndRenderHistory();
    }

    function closeHistoryModal() {
        historyModal.classList.remove("open");
    }

    document.getElementById("btnOpenEvalHistory")?.addEventListener("click", openHistoryModal);
    document.getElementById("btnHeaderEvalHistory")?.addEventListener("click", openHistoryModal);
    document.getElementById("btnCloseEvalHistory")?.addEventListener("click", closeHistoryModal);
    historyModal.addEventListener("click", (e) => {
        if (e.target === historyModal) closeHistoryModal();
    });

    document.getElementById("btnRefreshHistory")?.addEventListener("click", loadAndRenderHistory);
    document.getElementById("selHistoryPresetFilter")?.addEventListener("change", loadAndRenderHistory);

    async function loadAndRenderHistory() {
        const filterPreset = document.getElementById("selHistoryPresetFilter")?.value || "";

        try {
            // 1. Fetch summary
            const resSum = await fetch("/api/feedback/summary");
            const dataSum = await resSum.json();
            const summary = dataSum.summary || {};

            document.getElementById("summaryTotalCount").textContent = summary.total_evaluations || 0;
            document.getElementById("summaryAvgParity").textContent = `${summary.average_elevenlabs_parity || 0.0} / 10`;
            document.getElementById("summaryAvgSmoothness").textContent = `${summary.averages?.smoothness || 0.0} / 10`;
            document.getElementById("summaryAvgRealism").textContent = `${summary.averages?.realism || 0.0} / 10`;

            // Populate preset filter dropdown
            const filterSelect = document.getElementById("selHistoryPresetFilter");
            if (filterSelect && filterSelect.options.length <= 1) {
                Object.keys(summary.preset_counts || {}).forEach(name => {
                    const opt = document.createElement("option");
                    opt.value = name;
                    opt.textContent = `${name} (${summary.preset_counts[name]})`;
                    filterSelect.appendChild(opt);
                });
            }

            // 2. Fetch records
            const url = filterPreset ? `/api/feedback?preset_id=${encodeURIComponent(filterPreset)}` : "/api/feedback";
            const resList = await fetch(url);
            const dataList = await resList.json();
            const records = dataList.evaluations || [];

            const tbody = document.getElementById("evalHistoryTableBody");
            tbody.innerHTML = "";

            if (records.length === 0) {
                tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 18px;">No evaluations recorded yet.</td></tr>`;
                return;
            }

            records.forEach(r => {
                const tr = document.createElement("tr");

                const dateStr = new Date(r.timestamp).toLocaleDateString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
                const sc = r.scores || {};

                const getBadgeClass = (score) => {
                    if (score >= 8) return "score-high";
                    if (score >= 5) return "score-mid";
                    return "score-low";
                };

                const tagsHtml = (r.tags || []).map(t => `<span class="badge" style="font-size: 0.65rem; margin-right: 4px;">${t}</span>`).join("");
                const notesHtml = r.notes ? `<div style="font-style: italic; color: var(--text-main); margin-top: 4px;">"${r.notes}"</div>` : "";

                tr.innerHTML = `
                    <td style="white-space: nowrap; color: var(--text-dim);">${dateStr}</td>
                    <td><strong>${r.preset_name || "Custom"}</strong><br><span style="font-size: 0.65rem; color: var(--text-dim);">${r.language || ""}</span></td>
                    <td><span class="badge">${(r.engine_mode || "neural").toUpperCase()}</span></td>
                    <td><span class="score-badge ${getBadgeClass(sc.elevenlabs_parity)}">${sc.elevenlabs_parity || "-"}/10</span></td>
                    <td><span class="score-badge ${getBadgeClass(sc.smoothness)}">${sc.smoothness || "-"}/10</span></td>
                    <td><span class="score-badge ${getBadgeClass(sc.realism)}">${sc.realism || "-"}/10</span></td>
                    <td><span class="score-badge ${getBadgeClass(sc.pronunciation)}">${sc.pronunciation || "-"}/10</span></td>
                    <td>${tagsHtml}${notesHtml}</td>
                    <td>
                        <button type="button" class="btn-delete-eval" data-id="${r.id}" title="Delete Evaluation">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                `;

                tr.querySelector(".btn-delete-eval")?.addEventListener("click", async () => {
                    if (confirm("Delete this evaluation record?")) {
                        await fetch(`/api/feedback/${r.id}`, { method: "DELETE" });
                        await loadAndRenderHistory();
                        await updateEvaluationCounters();
                    }
                });

                tbody.appendChild(tr);
            });
        } catch (e) {
            console.error("Error loading evaluation history:", e);
        }
    }

    // Initial load
    initRatingPills();
    await populateFeedbackStoreFromBackend();
    await loadSymbols();
    await loadPresets();
    await updateEvaluationCounters();

    // Hook engine mode changes to evaluation context
    document.getElementById("selectEngineMode")?.addEventListener("change", (e) => {
        const presetId = document.getElementById("presetSelect")?.value;
        const p = presets.find(item => item.id === presetId);
        updateEvalContext(p, e.target.value, currentScript);
    });
});

