"""
API endpoint test script using starlette TestClient.
"""

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    print("[OK] /api/health passed")


def test_symbols():
    res = client.get("/api/symbols")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 20
    print(f"[OK] /api/symbols passed ({data['count']} symbols)")


def test_presets():
    res = client.get("/api/presets")
    assert res.status_code == 200
    presets = res.json()["presets"]
    assert len(presets) >= 4
    print(f"[OK] /api/presets passed ({len(presets)} presets)")


def test_synthesize():
    # Test with feline preset
    res_presets = client.get("/api/presets")
    first_preset = res_presets.json()["presets"][0]
    
    res = client.post("/api/synthesize", json={"script_json": first_preset["json_data"]})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "audio_base64" in data
    assert data["telemetry"]["duration_sec"] > 0
    print(f"[OK] /api/synthesize passed (duration: {data['telemetry']['duration_sec']:.2f}s)")

    # Test WAV direct endpoint
    res_wav = client.post("/api/synthesize/wav", json={"script_json": first_preset["json_data"]})
    assert res_wav.status_code == 200
    assert res_wav.headers["content-type"] == "audio/wav"
    assert len(res_wav.content) > 1000
    print(f"[OK] /api/synthesize/wav passed ({len(res_wav.content)} bytes)")


if __name__ == "__main__":
    test_health()
    test_symbols()
    test_presets()
    test_synthesize()
    print("\n==========================================")
    print("  ALL API ENDPOINTS VERIFIED AND WORKING  ")
    print("==========================================")
