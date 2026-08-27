"""
FastAPI Backend Server for Universal Phonetic Speech Studio.
Provides REST APIs for script synthesis (Neural-Bioacoustic Hybrid and High-Definition DSP modes),
presets, and symbol reference metadata.
"""

import os
import glob
import base64
import yaml
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Body, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .engine import (
    ConlangScript,
    synthesize_script,
    synthesize_neural_script,
    synthesize_neural_script_async,
    audio_to_wav_bytes,
    get_all_symbols_metadata,
)


app = FastAPI(
    title="Universal Phonetic Speech Synthesis Studio",
    version="1.0.0",
    description="API for synthesizing conlangs, artificial languages, animal vocalizations, and expressive tones."
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PRESETS_DIR = os.path.join(os.path.dirname(__file__), "presets")


class SynthesizeRequest(BaseModel):
    script_yaml: Optional[str] = None
    script_json: Optional[Dict[str, Any]] = None
    engine_mode: Optional[str] = "neural"  # 'neural' (Ultra-Realistic Hybrid) or 'dsp' (Parametric DSP)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "Universal Phonetic Speech Studio"}


@app.get("/api/symbols")
async def get_symbols():
    """Returns all vowel, consonant, non-pulmonic, and creature symbols with IPA metadata."""
    symbols = get_all_symbols_metadata()
    return {"count": len(symbols), "symbols": symbols}


@app.get("/api/presets")
async def list_presets():
    """Returns all available conlang script presets."""
    presets = []
    for filepath in sorted(glob.glob(os.path.join(PRESETS_DIR, "*.yaml"))):
        filename = os.path.basename(filepath)
        preset_id = os.path.splitext(filename)[0]
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                data = yaml.safe_load(content)
            presets.append({
                "id": preset_id,
                "name": data.get("language", preset_id),
                "description": data.get("description", ""),
                "yaml_content": content,
                "json_data": data,
            })
        except Exception as e:
            print(f"Error loading preset {filepath}: {e}")
    return {"presets": presets}


@app.post("/api/synthesize")
async def synthesize_endpoint(req: SynthesizeRequest):
    """
    Synthesizes speech from either YAML string or JSON object.
    Supports 'neural' (Ultra-Realistic Neural-Bioacoustic Hybrid) and 'dsp' (Parametric DSP) modes.
    Returns base64 WAV audio and telemetry.
    """
    try:
        if req.script_yaml:
            data = yaml.safe_load(req.script_yaml)
        elif req.script_json:
            data = req.script_json
        else:
            raise HTTPException(status_code=400, detail="Must provide script_yaml or script_json")

        script = ConlangScript(**data)

        # Select synthesis engine mode
        mode = (req.engine_mode or "neural").lower()
        if mode == "neural":
            try:
                audio, telemetry = await synthesize_neural_script_async(script)
            except Exception as e:
                print(f"[Neural Fallback to DSP] {e}")
                audio, telemetry = synthesize_script(script)
        else:
            audio, telemetry = synthesize_script(script)

        wav_bytes = audio_to_wav_bytes(audio)
        b64_audio = base64.b64encode(wav_bytes).decode("utf-8")

        return {
            "status": "success",
            "audio_base64": f"data:audio/wav;base64,{b64_audio}",
            "telemetry": telemetry,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/synthesize/wav")
async def synthesize_wav_direct(req: SynthesizeRequest):
    """Direct WAV audio streaming endpoint for downloads."""
    try:
        if req.script_yaml:
            data = yaml.safe_load(req.script_yaml)
        elif req.script_json:
            data = req.script_json
        else:
            raise HTTPException(status_code=400, detail="Must provide script_yaml or script_json")

        script = ConlangScript(**data)
        mode = (req.engine_mode or "neural").lower()
        if mode == "neural":
            try:
                audio, _ = await synthesize_neural_script_async(script)
            except Exception:
                audio, _ = synthesize_script(script)
        else:
            audio, _ = synthesize_script(script)

        wav_bytes = audio_to_wav_bytes(audio)
        return Response(content=wav_bytes, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Mount frontend static files
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
