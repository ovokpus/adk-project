import pytest
from fastapi.testclient import TestClient

import settings
from server import api


@pytest.fixture
def client(monkeypatch):
    for v in ["GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_GENAI_USE_ENTERPRISE"]:
        monkeypatch.delenv(v, raising=False)
    return TestClient(api.app)


def test_agents_listed_with_structure(client):
    agents = {a["id"]: a for a in client.get("/api/agents").json()}
    assert set(agents) == {"my_google_search_agent", "geo_validator", "llm_auditor", "app_agent"}
    assert agents["geo_validator"]["output_schema"]["required"] == ["capital"]
    assert [s["name"] for s in agents["llm_auditor"]["sub_agents"]] == ["critic_agent", "reviser_agent"]


def test_run_without_credentials_is_503_and_not_simulated(client):
    r = client.post("/api/agents/geo_validator/run", json={"message": "capital of France?"})
    assert r.status_code == 503
    assert r.json()["detail"]["configured"] is False
    assert "simulated" in r.json()["detail"]["note"]


def test_llm_status_modes(monkeypatch):
    for v in ["GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_GENAI_USE_ENTERPRISE"]:
        monkeypatch.delenv(v, raising=False)
    assert settings.llm_status()["configured"] is False
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    assert settings.llm_status()["backend"] == "gemini-api"
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "true")
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    s = settings.llm_status()
    assert s["backend"] == "vertex" and not s["configured"]


def test_validate_output(client):
    ok = client.post("/api/agents/geo_validator/validate-output", json={"raw": '{"capital": "Tokyo"}'}).json()
    bad = client.post("/api/agents/geo_validator/validate-output", json={"raw": '{"city": "Tokyo"}'}).json()
    assert ok == {"valid": True, "parsed": {"capital": "Tokyo"}}
    assert bad["valid"] is False and bad["errors"][0]["loc"] == ["capital"]
    assert client.post("/api/agents/app_agent/validate-output", json={"raw": "{}"}).status_code == 404


def test_reviser_callback_endpoint(client):
    r = client.post("/api/callbacks/reviser-end-of-edit", json={"text": "A\n---END-OF-EDIT---\nB"}).json()
    assert r["output"] == "A\n"
