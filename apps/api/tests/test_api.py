from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_calendar_and_ruleset_endpoint():
    calendar = client.get("/api/v1/calendar", params={"season": 2026})
    assert calendar.status_code == 200
    assert len(calendar.json()["rounds"]) >= 10

    ruleset = client.get("/api/v1/ruleset/current")
    assert ruleset.status_code == 200
    assert ruleset.json()["season"] == 2026


def test_simulation_run_and_fetch_predictions():
    run = client.post(
        "/api/v1/simulations/run", json={"season": 2026, "round": 2, "n_sims": 10000}
    )
    assert run.status_code == 200
    run_id = run.json()["run_id"]

    predictions = client.get(f"/api/v1/simulations/{run_id}/predictions")
    assert predictions.status_code == 200
    assert len(predictions.json()["predictions"]) > 0
