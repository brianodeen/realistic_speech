"""
Speech Synthesis Evaluation & Feedback Storage Engine.
Handles persistent storage, retrieval, and aggregation of 1-10 quality metric evaluations,
diagnostic issue tags, and qualitative user notes benchmarked against ElevenLabs parity.
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
FEEDBACK_FILE = os.path.join(DATA_DIR, "evaluations.json")


class MetricScores(BaseModel):
    smoothness: int = Field(..., ge=1, le=10, description="Smoothness & Cursive Flow (1-10)")
    realism: int = Field(..., ge=1, le=10, description="Realism & Fleshiness (1-10)")
    pronunciation: int = Field(..., ge=1, le=10, description="Pronunciation & Articulatory Precision (1-10)")
    prosody: int = Field(..., ge=1, le=10, description="Prosody & Intonation Expressiveness (1-10)")
    bioacoustics: Optional[int] = Field(default=None, ge=1, le=10, description="Extended Bioacoustic & Alien Authenticity (1-10 or None)")
    cleanliness: int = Field(..., ge=1, le=10, description="Acoustic Cleanliness & Clarity (1-10)")
    elevenlabs_parity: int = Field(..., ge=1, le=10, description="Overall ElevenLabs-Parity Benchmark (1-10)")


class EvaluationSubmission(BaseModel):
    preset_id: Optional[str] = "custom"
    preset_name: Optional[str] = "Custom Script"
    language: Optional[str] = "Conlang"
    engine_mode: str = Field(default="neural", description="'neural' or 'dsp'")
    script_text: str = Field(default="", description="The ExtIPA or YAML script evaluated")
    scores: MetricScores
    tags: List[str] = Field(default_factory=list, description="Diagnostic issue flags")
    notes: Optional[str] = Field(default="", description="Qualitative feedback notes")
    speaker_params: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EvaluationRecord(BaseModel):
    id: str
    timestamp: str
    preset_id: str
    preset_name: str
    language: str
    engine_mode: str
    script_text: str
    scores: MetricScores
    tags: List[str]
    notes: str
    speaker_params: Dict[str, Any]


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def load_evaluations() -> List[Dict[str, Any]]:
    """Loads all evaluation records from persistent storage."""
    _ensure_data_dir()
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Feedback Warning] Failed to read {FEEDBACK_FILE}: {e}")
        return []


def save_evaluation(sub: EvaluationSubmission) -> EvaluationRecord:
    """Saves a new evaluation record persistently."""
    _ensure_data_dir()
    records = load_evaluations()

    record_dict = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "preset_id": sub.preset_id or "custom",
        "preset_name": sub.preset_name or "Custom Script",
        "language": sub.language or "Conlang",
        "engine_mode": sub.engine_mode,
        "script_text": sub.script_text,
        "scores": sub.scores.model_dump(),
        "tags": sub.tags or [],
        "notes": sub.notes or "",
        "speaker_params": sub.speaker_params or {},
    }

    records.insert(0, record_dict)

    # Atomic write to temporary file then replace
    tmp_path = FEEDBACK_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, FEEDBACK_FILE)

    return EvaluationRecord(**record_dict)


def delete_evaluation(eval_id: str) -> bool:
    """Deletes an evaluation record by ID."""
    _ensure_data_dir()
    records = load_evaluations()
    filtered = [r for r in records if r.get("id") != eval_id]
    if len(filtered) == len(records):
        return False

    tmp_path = FEEDBACK_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, FEEDBACK_FILE)
    return True


def get_evaluation_summary() -> Dict[str, Any]:
    """Computes summary statistics and averages across all evaluations."""
    records = load_evaluations()
    if not records:
        return {
            "total_evaluations": 0,
            "average_elevenlabs_parity": 0.0,
            "averages": {},
            "preset_counts": {},
            "top_issues": {},
        }

    keys = ["smoothness", "realism", "pronunciation", "prosody", "cleanliness", "elevenlabs_parity"]
    totals = {k: 0.0 for k in keys}
    counts = {k: 0 for k in keys}

    bio_total = 0.0
    bio_count = 0

    preset_counts = {}
    issue_counts = {}

    for r in records:
        sc = r.get("scores", {})
        for k in keys:
            if k in sc and sc[k] is not None:
                totals[k] += float(sc[k])
                counts[k] += 1
        if "bioacoustics" in sc and sc["bioacoustics"] is not None:
            bio_total += float(sc["bioacoustics"])
            bio_count += 1

        p_name = r.get("preset_name", "Unknown")
        preset_counts[p_name] = preset_counts.get(p_name, 0) + 1

        for t in r.get("tags", []):
            issue_counts[t] = issue_counts.get(t, 0) + 1

    averages = {}
    for k in keys:
        averages[k] = round(totals[k] / max(1, counts[k]), 2) if counts[k] > 0 else 0.0

    if bio_count > 0:
        averages["bioacoustics"] = round(bio_total / bio_count, 2)
    else:
        averages["bioacoustics"] = None

    # Sort top issues
    sorted_issues = dict(sorted(issue_counts.items(), key=lambda item: item[1], reverse=True))

    return {
        "total_evaluations": len(records),
        "average_elevenlabs_parity": averages.get("elevenlabs_parity", 0.0),
        "averages": averages,
        "preset_counts": preset_counts,
        "top_issues": sorted_issues,
    }
