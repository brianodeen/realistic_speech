"""
Unit tests for the Speech Synthesis Evaluation & Feedback System.
Tests 1-10 metric validations, JSON persistence, summary aggregation, and API routes.
"""

import os
import json
import os
import json
from fastapi.testclient import TestClient

from backend.app import app
from backend.engine.feedback import (
    MetricScores,
    EvaluationSubmission,
    save_evaluation,
    load_evaluations,
    delete_evaluation,
    get_evaluation_summary,
    FEEDBACK_FILE,
)

client = TestClient(app)


def test_metric_scores_validation():
    # Valid scores
    valid = MetricScores(
        smoothness=8,
        realism=7,
        pronunciation=9,
        prosody=8,
        bioacoustics=6,
        cleanliness=9,
        elevenlabs_parity=8,
    )
    assert valid.smoothness == 8
    assert valid.elevenlabs_parity == 8

    # Bioacoustics can be None for pure human speech
    human_valid = MetricScores(
        smoothness=9,
        realism=9,
        pronunciation=10,
        prosody=9,
        bioacoustics=None,
        cleanliness=10,
        elevenlabs_parity=9,
    )
    assert human_valid.bioacoustics is None

    # Out of bounds (> 10)
    failed_high = False
    try:
        MetricScores(
            smoothness=11,
            realism=5,
            pronunciation=5,
            prosody=5,
            bioacoustics=5,
            cleanliness=5,
            elevenlabs_parity=5,
        )
    except Exception:
        failed_high = True
    assert failed_high, "Expected validation error for score > 10"

    # Out of bounds (< 1)
    failed_low = False
    try:
        MetricScores(
            smoothness=0,
            realism=5,
            pronunciation=5,
            prosody=5,
            bioacoustics=5,
            cleanliness=5,
            elevenlabs_parity=5,
        )
    except Exception:
        failed_low = True
    assert failed_low, "Expected validation error for score < 1"


def test_save_and_load_evaluation():
    sub = EvaluationSubmission(
        preset_id="test_preset",
        preset_name="Test Preset Language",
        language="Testish",
        engine_mode="neural",
        script_text="wiː‿sɔː juː‿ɡoʊ",
        scores=MetricScores(
            smoothness=9,
            realism=8,
            pronunciation=9,
            prosody=8,
            bioacoustics=None,
            cleanliness=10,
            elevenlabs_parity=8,
        ),
        tags=["Test Tag"],
        notes="Testing feedback persistence",
    )

    rec = save_evaluation(sub)
    assert rec.id
    assert rec.preset_name == "Test Preset Language"
    assert rec.scores.elevenlabs_parity == 8

    # Verify it exists in file
    records = load_evaluations()
    found = [r for r in records if r["id"] == rec.id]
    assert len(found) == 1
    assert found[0]["notes"] == "Testing feedback persistence"

    # Test deletion
    deleted = delete_evaluation(rec.id)
    assert deleted is True

    records_after = load_evaluations()
    assert not any(r["id"] == rec.id for r in records_after)


def test_api_feedback_endpoints():
    # 1. Post feedback via API
    payload = {
        "preset_id": "alien_click_tonal",
        "preset_name": "Xylos (Tonal Click Conlang)",
        "language": "Xylos",
        "engine_mode": "neural",
        "script_text": "kǀiː‿ʃuː ʔkǃaː‿kǁuː",
        "scores": {
            "smoothness": 8,
            "realism": 8,
            "pronunciation": 9,
            "prosody": 8,
            "bioacoustics": 7,
            "cleanliness": 9,
            "elevenlabs_parity": 8,
        },
        "tags": ["Click release sharp"],
        "notes": "Good click articulation on dental click",
    }

    res = client.post("/api/feedback", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    eval_id = data["record"]["id"]

    # 2. Get feedback list
    res_list = client.get("/api/feedback")
    assert res_list.status_code == 200
    evals = res_list.json()["evaluations"]
    assert any(e["id"] == eval_id for e in evals)

    # 3. Get feedback summary
    res_sum = client.get("/api/feedback/summary")
    assert res_sum.status_code == 200
    sum_data = res_sum.json()["summary"]
    assert sum_data["total_evaluations"] >= 1
    assert sum_data["average_elevenlabs_parity"] >= 1.0

    # 4. Clean up created record
    res_del = client.delete(f"/api/feedback/{eval_id}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "success"


if __name__ == "__main__":
    test_metric_scores_validation()
    test_save_and_load_evaluation()
    test_api_feedback_endpoints()
    print("\n==========================================")
    print("  ALL FEEDBACK API TESTS PASSED!  ")
    print("==========================================")
