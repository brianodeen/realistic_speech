/**
 * WebAudio Synthesizer Engine for client-side instant previewing.
 */

class WebAudioSynth {
    constructor() {
        this.ctx = null;
        this.isPlaying = false;
        this.currentSource = null;
    }

    init() {
        if (!this.ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.ctx = new AudioContext();
        }
        if (this.ctx.state === "suspended") {
            this.ctx.resume();
        }
    }

    stop() {
        if (this.currentSource) {
            try {
                this.currentSource.stop();
            } catch (e) {}
            this.currentSource = null;
        }
        this.isPlaying = false;
    }

    async playWavData(base64Data, onEnded) {
        this.init();
        this.stop();

        // Convert base64 data URL to ArrayBuffer
        const base64Str = base64Data.split(",")[1];
        const binaryString = window.atob(base64Str);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }

        const audioBuffer = await this.ctx.decodeAudioData(bytes.buffer);
        const source = this.ctx.createBufferSource();
        source.buffer = audioBuffer;

        // Connect through master gain
        const gain = this.ctx.createGain();
        gain.gain.value = 1.0;
        source.connect(gain);
        gain.connect(this.ctx.destination);

        source.onended = () => {
            this.isPlaying = false;
            if (onEnded) onEnded();
        };

        this.currentSource = source;
        this.isPlaying = true;
        source.start(0);

        return {
            duration: audioBuffer.duration,
            buffer: audioBuffer
        };
    }
}

window.WebAudioSynth = WebAudioSynth;
