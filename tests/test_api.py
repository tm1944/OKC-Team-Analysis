# ruff: noqa: E501
from fastapi.testclient import TestClient

from basketball_api.app import app, get_analysis_service


class FakeService:
    def analyze(self, request):
        return {"player": {"name": request.player}, "question": request.question, "filters_applied": {}, "statistics": {}, "model_prediction": {"status": "not_requested"}, "retrieved_evidence": [], "generated_analysis": "fake", "limitations": []}


def test_analyze_player_uses_injected_service() -> None:
    app.dependency_overrides[get_analysis_service] = lambda: FakeService()
    client = TestClient(app)

    response = client.post("/analyze-player", json={"player": "Shai Gilgeous-Alexander", "question": "How is he?"})

    assert response.status_code == 200
    assert response.json()["generated_analysis"] == "fake"
    app.dependency_overrides.clear()


def test_shot_context_requires_all_fields() -> None:
    client = TestClient(app)

    response = client.post("/analyze-player", json={"player": "Shai", "question": "test", "shot_context": {"shot_distance_ft": 3}})

    assert response.status_code == 422
