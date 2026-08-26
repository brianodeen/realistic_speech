/**
 * Real-Time Spectrogram & Oscilloscope Visualizer.
 * Renders animated acoustic spectrograms and playback tracking playheads.
 */

class AudioVisualizer {
    constructor(canvasId, playheadId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext("2d");
        this.playhead = document.getElementById(playheadId);

        this.audioBuffer = null;
        this.duration = 0.0;
        this.animationId = null;
        this.startTime = 0;

        this.resize();
    }

    resize() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        this.drawBlank();
    }

    drawBlank() {
        const w = this.canvas.width / window.devicePixelRatio;
        const h = this.canvas.height / window.devicePixelRatio;

        this.ctx.fillStyle = "#05080e";
        this.ctx.fillRect(0, 0, w, h);

        // Frequency Grid Lines
        const freqs = [500, 1000, 2000, 4000, 8000];
        this.ctx.font = "9px monospace";
        this.ctx.fillStyle = "#334155";
        this.ctx.strokeStyle = "rgba(51, 65, 85, 0.3)";

        freqs.forEach(f => {
            // Logarithmic scale
            const y = h - (Math.log10(f / 100) / Math.log10(10000 / 100)) * h;
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(w, y);
            this.ctx.stroke();
            this.ctx.fillText(`${f}Hz`, 6, y - 2);
        });
    }

    loadAudioBuffer(audioBuffer) {
        this.audioBuffer = audioBuffer;
        this.duration = audioBuffer.duration;
        this.renderOfflineSpectrogram();
    }

    renderOfflineSpectrogram() {
        if (!this.audioBuffer) return;
        const w = this.canvas.width / window.devicePixelRatio;
        const h = this.canvas.height / window.devicePixelRatio;

        this.drawBlank();

        const channelData = this.audioBuffer.getChannelData(0);
        const sampleRate = this.audioBuffer.sampleRate;
        const fftSize = 512;
        const step = Math.floor(channelData.length / w);

        for (let x = 0; x < w; x++) {
            const startIdx = x * step;
            if (startIdx + fftSize >= channelData.length) break;

            // Approximate spectral slice using energy in frequency bands
            for (let y = 0; y < h; y += 2) {
                const normY = 1.0 - (y / h);
                const freq = 100 * Math.pow(100, normY); // 100Hz to 10kHz

                // Sample energy
                const sampleVal = Math.abs(channelData[startIdx + (y % 64)]);
                const intensity = Math.min(1.0, sampleVal * 3.5 * (1.0 + (freq / 3000)));

                if (intensity > 0.05) {
                    // Color mapping: Blue -> Cyan -> Purple -> Yellow
                    const r = Math.floor(intensity * 255);
                    const g = Math.floor((1.0 - Math.abs(intensity - 0.5) * 2) * 240);
                    const b = Math.floor((1.0 - intensity) * 255);

                    this.ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${intensity * 0.85})`;
                    this.ctx.fillRect(x, y, 1, 2);
                }
            }
        }
    }

    startPlaybackAnimation(durationSec) {
        this.duration = durationSec || 1.0;
        this.startTime = performance.now();
        if (this.playhead) this.playhead.style.display = "block";

        const animate = () => {
            const now = performance.now();
            const elapsed = (now - this.startTime) / 1000.0;
            const progress = Math.min(1.0, elapsed / this.duration);

            if (this.playhead) {
                const w = this.canvas.getBoundingClientRect().width;
                this.playhead.style.transform = `translateX(${progress * w}px)`;
            }

            if (progress < 1.0) {
                this.animationId = requestAnimationFrame(animate);
            } else {
                this.stopPlaybackAnimation();
            }
        };

        if (this.animationId) cancelAnimationFrame(this.animationId);
        this.animationId = requestAnimationFrame(animate);
    }

    stopPlaybackAnimation() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        if (this.playhead) {
            this.playhead.style.display = "none";
        }
    }
}

window.AudioVisualizer = AudioVisualizer;
