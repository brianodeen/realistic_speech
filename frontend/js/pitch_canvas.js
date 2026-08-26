/**
 * Interactive Tone & Pitch Contour Spline Canvas.
 * Handles Chao 5-level tones, custom Bézier points, and interactive curve drawing.
 */

class PitchCanvas {
    constructor(canvasId, onCurveChanged) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext("2d");
        this.onCurveChanged = onCurveChanged;

        this.points = [
            [0.0, 160],
            [1.0, 160]
        ];
        this.basePitch = 140;
        this.pitchRange = 12; // semitones
        this.activeTone = "custom";

        this.selectedPointIdx = -1;
        this.isDragging = false;

        this.initCanvasEvents();
        this.resize();
    }

    resize() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        this.draw();
    }

    setSpeaker(basePitch, pitchRange) {
        this.basePitch = basePitch || 140;
        this.pitchRange = pitchRange || 12;
        this.draw();
    }

    setSyllableProsody(prosody) {
        if (!prosody) return;
        this.activeTone = prosody.chao_tone || "custom";

        if (prosody.pitch_curve && prosody.pitch_curve.length >= 2) {
            this.points = JSON.parse(JSON.stringify(prosody.pitch_curve));
            this.activeTone = "custom";
        } else if (prosody.chao_tone) {
            this.setChaoTone(prosody.chao_tone, false);
        } else {
            this.points = [
                [0.0, this.basePitch],
                [1.0, this.basePitch]
            ];
        }
        this.draw();
    }

    setChaoTone(toneCode, triggerCallback = true) {
        this.activeTone = toneCode;
        const semiToHz = (st) => this.basePitch * Math.pow(2.0, (st * (this.pitchRange / 12.0)) / 12.0);

        const chaoMap = {
            "55": [[0.0, semiToHz(6)], [1.0, semiToHz(6)]],
            "35": [[0.0, semiToHz(0)], [0.3, semiToHz(1)], [1.0, semiToHz(6)]],
            "214": [[0.0, semiToHz(-3)], [0.4, semiToHz(-6)], [1.0, semiToHz(3)]],
            "51": [[0.0, semiToHz(6)], [0.2, semiToHz(4)], [1.0, semiToHz(-6)]],
            "33": [[0.0, semiToHz(0)], [1.0, semiToHz(0)]],
            "11": [[0.0, semiToHz(-6)], [1.0, semiToHz(-6)]],
        };

        if (chaoMap[toneCode]) {
            this.points = chaoMap[toneCode];
        }

        this.draw();
        if (triggerCallback && this.onCurveChanged) {
            this.onCurveChanged(this.points, this.activeTone);
        }
    }

    // Coordinate transformations
    valToCanvas(timeRatio, hz) {
        const w = this.canvas.width / window.devicePixelRatio;
        const h = this.canvas.height / window.devicePixelRatio;

        const padX = 40;
        const padY = 25;

        const x = padX + timeRatio * (w - padX * 2);

        // F0 display range: basePitch / 2 to basePitch * 2
        const minHz = Math.max(40, this.basePitch * 0.5);
        const maxHz = this.basePitch * 2.2;
        const yNorm = (hz - minHz) / (maxHz - minHz);
        const y = (h - padY) - yNorm * (h - padY * 2);

        return { x, y };
    }

    canvasToVal(x, y) {
        const w = this.canvas.width / window.devicePixelRatio;
        const h = this.canvas.height / window.devicePixelRatio;

        const padX = 40;
        const padY = 25;

        const timeRatio = Math.max(0.0, Math.min(1.0, (x - padX) / (w - padX * 2)));

        const minHz = Math.max(40, this.basePitch * 0.5);
        const maxHz = this.basePitch * 2.2;
        const yNorm = Math.max(0.0, Math.min(1.0, ((h - padY) - y) / (h - padY * 2)));
        const hz = Math.round(minHz + yNorm * (maxHz - minHz));

        return { timeRatio, hz };
    }

    initCanvasEvents() {
        const getPos = (e) => {
            const rect = this.canvas.getBoundingClientRect();
            return {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
        };

        this.canvas.addEventListener("mousedown", (e) => {
            const { x, y } = getPos(e);
            let closestIdx = -1;
            let minDist = 14;

            this.points.forEach((p, idx) => {
                const pos = this.valToCanvas(p[0], p[1]);
                const dist = Math.hypot(pos.x - x, pos.y - y);
                if (dist < minDist) {
                    minDist = dist;
                    closestIdx = idx;
                }
            });

            if (closestIdx >= 0) {
                this.selectedPointIdx = closestIdx;
                this.isDragging = true;
            }
        });

        window.addEventListener("mousemove", (e) => {
            if (!this.isDragging || this.selectedPointIdx < 0) return;
            const { x, y } = getPos(e);
            const val = this.canvasToVal(x, y);

            // Keep endpoints locked to 0.0 and 1.0
            if (this.selectedPointIdx === 0) {
                val.timeRatio = 0.0;
            } else if (this.selectedPointIdx === this.points.length - 1) {
                val.timeRatio = 1.0;
            }

            this.points[this.selectedPointIdx] = [val.timeRatio, val.hz];
            this.points.sort((a, b) => a[0] - b[0]);
            this.activeTone = "custom";
            this.draw();

            if (this.onCurveChanged) {
                this.onCurveChanged(this.points, this.activeTone);
            }
        });

        window.addEventListener("mouseup", () => {
            this.isDragging = false;
            this.selectedPointIdx = -1;
        });

        // Double click to insert new point
        this.canvas.addEventListener("dblclick", (e) => {
            const { x, y } = getPos(e);
            const val = this.canvasToVal(x, y);

            if (val.timeRatio > 0.05 && val.timeRatio < 0.95) {
                this.points.push([val.timeRatio, val.hz]);
                this.points.sort((a, b) => a[0] - b[0]);
                this.activeTone = "custom";
                this.draw();
                if (this.onCurveChanged) {
                    this.onCurveChanged(this.points, this.activeTone);
                }
            }
        });
    }

    draw() {
        const w = this.canvas.width / window.devicePixelRatio;
        const h = this.canvas.height / window.devicePixelRatio;

        this.ctx.clearRect(0, 0, w, h);

        const padX = 40;
        const padY = 25;

        // 1. Draw Chao 5-Level Grid Lines
        const chaoLevels = [
            { level: "5", name: "High (5)", st: 6.0, color: "rgba(168, 85, 247, 0.4)" },
            { level: "4", name: "Half-High (4)", st: 3.0, color: "rgba(59, 130, 246, 0.25)" },
            { level: "3", name: "Mid (3)", st: 0.0, color: "rgba(0, 240, 255, 0.4)" },
            { level: "2", name: "Half-Low (2)", st: -3.0, color: "rgba(59, 130, 246, 0.25)" },
            { level: "1", name: "Low (1)", st: -6.0, color: "rgba(168, 85, 247, 0.4)" },
        ];

        this.ctx.font = "10px monospace";
        chaoLevels.forEach(cl => {
            const hz = this.basePitch * Math.pow(2.0, (cl.st * (this.pitchRange / 12.0)) / 12.0);
            const pos = this.valToCanvas(0.0, hz);

            this.ctx.strokeStyle = cl.color;
            this.ctx.setLineDash([4, 4]);
            this.ctx.beginPath();
            this.ctx.moveTo(padX, pos.y);
            this.ctx.lineTo(w - padX, pos.y);
            this.ctx.stroke();
            this.ctx.setLineDash([]);

            // Label
            this.ctx.fillStyle = "#64748b";
            this.ctx.fillText(`${cl.level} (${Math.round(hz)}Hz)`, 4, pos.y + 3);
        });

        // 2. Draw Pitch Contour Curve
        if (this.points.length >= 2) {
            this.ctx.strokeStyle = "#00f0ff";
            this.ctx.lineWidth = 3;
            this.ctx.shadowColor = "#00f0ff";
            this.ctx.shadowBlur = 10;

            this.ctx.beginPath();
            const startPos = this.valToCanvas(this.points[0][0], this.points[0][1]);
            this.ctx.moveTo(startPos.x, startPos.y);

            for (let i = 0; i < this.points.length - 1; i++) {
                const p0 = this.valToCanvas(this.points[i][0], this.points[i][1]);
                const p1 = this.valToCanvas(this.points[i + 1][0], this.points[i + 1][1]);
                const midX = (p0.x + p1.x) / 2;
                this.ctx.bezierCurveTo(midX, p0.y, midX, p1.y, p1.x, p1.y);
            }
            this.ctx.stroke();
            this.ctx.shadowBlur = 0; // reset

            // 3. Draw Control Handles
            this.points.forEach((p, idx) => {
                const pos = this.valToCanvas(p[0], p[1]);

                this.ctx.fillStyle = idx === this.selectedPointIdx ? "#ff007f" : "#ffffff";
                this.ctx.strokeStyle = "#00f0ff";
                this.ctx.lineWidth = 2;

                this.ctx.beginPath();
                this.ctx.arc(pos.x, pos.y, 5.5, 0, Math.PI * 2);
                this.ctx.fill();
                this.ctx.stroke();

                // F0 Text above point
                this.ctx.fillStyle = "#38bdf8";
                this.ctx.fillText(`${Math.round(p[1])}Hz`, pos.x - 12, pos.y - 10);
            });
        }
    }
}

window.PitchCanvas = PitchCanvas;
