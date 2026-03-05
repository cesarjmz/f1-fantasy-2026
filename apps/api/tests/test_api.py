from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.main import app
from app.models.gameplay import FantasyTeam, PointsLedgerEntry
from app.models.reference import FantasyAssetPrice, MeetingRound
from app.models.simulation import SimulationRun


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_calendar_and_ruleset_endpoint():
    calendar = client.get("/api/v1/calendar", params={"season": 2026})
    assert calendar.status_code == 200
    assert len(calendar.json()["rounds"]) >= 10

    with SessionLocal() as db:
        persisted_round = db.scalar(
            select(MeetingRound).where(MeetingRound.season == 2026)
        )
        assert persisted_round is not None

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
    body = predictions.json()
    assert len(body["predictions"]) > 0
    assert body["n_sims"] == 10000
    assert body["meta"]["total"] == len(body["predictions"])
    assert body["meta"]["offset"] == 0
    assert body["meta"]["returned"] == len(body["predictions"])
    assert body["meta"]["has_more"] is False
    assert body["meta"]["next_offset"] is None
    assert body["summary"]["entity_count"] == len(body["predictions"])
    assert body["summary"]["top_mean"]["entity_id"] > 0
    assert body["summary"]["highest_upside"]["entity_id"] > 0
    assert body["summary"]["highest_negative_risk"]["entity_id"] > 0

    with SessionLocal() as db:
        persisted = db.scalar(
            select(SimulationRun).where(SimulationRun.run_id == run_id)
        )
        assert persisted is not None


def test_simulation_predictions_distribution_sanity_at_10k_sims():
    run = client.post(
        "/api/v1/simulations/run", json={"season": 2026, "round": 3, "n_sims": 10000}
    )
    assert run.status_code == 200
    run_id = run.json()["run_id"]

    predictions = client.get(f"/api/v1/simulations/{run_id}/predictions")
    assert predictions.status_code == 200

    payload = predictions.json()
    first = payload["predictions"][0]["summary"]
    assert first["p10"] <= first["median"] <= first["p90"]
    assert 0.0 <= first["prob_negative"] <= 1.0
    assert payload["summary"]["entity_count"] == len(payload["predictions"])


def test_simulation_summary_endpoint_returns_run_metadata_only():
    run = client.post(
        "/api/v1/simulations/run", json={"season": 2026, "round": 4, "n_sims": 10000}
    )
    assert run.status_code == 200
    run_id = run.json()["run_id"]

    summary = client.get(f"/api/v1/simulations/{run_id}/summary")
    assert summary.status_code == 200
    body = summary.json()

    assert body["run_id"] == run_id
    assert body["season"] == 2026
    assert body["round"] == 4
    assert body["n_sims"] == 10000
    assert body["summary"]["entity_count"] > 0
    assert body["summary"]["top_mean"]["entity_id"] > 0
    assert "predictions" not in body


def test_simulation_summary_endpoint_not_found_returns_typed_error():
    summary = client.get("/api/v1/simulations/not-a-real-run/summary")
    assert summary.status_code == 404
    body = summary.json()
    assert body["error"]["code"] == "simulation_run_not_found"
    assert body["error"]["message"] == "Unknown run_id"


def test_simulation_predictions_supports_limit_without_changing_summary_count():
    run = client.post(
        "/api/v1/simulations/run", json={"season": 2026, "round": 5, "n_sims": 10000}
    )
    assert run.status_code == 200
    run_id = run.json()["run_id"]

    full = client.get(f"/api/v1/simulations/{run_id}/predictions")
    assert full.status_code == 200
    full_json = full.json()

    limited = client.get(
        f"/api/v1/simulations/{run_id}/predictions", params={"limit": 3}
    )
    assert limited.status_code == 200
    limited_json = limited.json()

    assert len(limited_json["predictions"]) == 3
    assert limited_json["meta"]["total"] == len(full_json["predictions"])
    assert limited_json["meta"]["limit"] == 3
    assert limited_json["meta"]["offset"] == 0
    assert limited_json["meta"]["returned"] == 3
    assert limited_json["meta"]["has_more"] is True
    assert limited_json["meta"]["next_offset"] == 3
    assert (
        limited_json["summary"]["entity_count"] == full_json["summary"]["entity_count"]
    )
    assert limited_json["summary"] == full_json["summary"]


def test_simulation_predictions_supports_offset_pagination():
    run = client.post(
        "/api/v1/simulations/run", json={"season": 2026, "round": 7, "n_sims": 10000}
    )
    assert run.status_code == 200
    run_id = run.json()["run_id"]

    page_1 = client.get(
        f"/api/v1/simulations/{run_id}/predictions",
        params={"limit": 4, "offset": 0},
    )
    assert page_1.status_code == 200
    page_1_json = page_1.json()
    assert len(page_1_json["predictions"]) == 4
    assert page_1_json["meta"]["has_more"] is True
    assert page_1_json["meta"]["next_offset"] == 4

    page_2 = client.get(
        f"/api/v1/simulations/{run_id}/predictions",
        params={"limit": 4, "offset": 4},
    )
    assert page_2.status_code == 200
    page_2_json = page_2.json()
    assert len(page_2_json["predictions"]) == 4
    assert page_2_json["meta"]["offset"] == 4

    ids_1 = {item["entity_id"] for item in page_1_json["predictions"]}
    ids_2 = {item["entity_id"] for item in page_2_json["predictions"]}
    assert ids_1.isdisjoint(ids_2)


def test_simulation_predictions_limit_validation_returns_typed_error():
    run = client.post(
        "/api/v1/simulations/run", json={"season": 2026, "round": 6, "n_sims": 10000}
    )
    assert run.status_code == 200
    run_id = run.json()["run_id"]

    response = client.get(
        f"/api/v1/simulations/{run_id}/predictions", params={"limit": 0}
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"


def test_assets_prices_persisted():
    prices = client.get("/api/v1/assets/prices", params={"season": 2026, "round": 2})
    assert prices.status_code == 200
    assert len(prices.json()["assets"]) > 0

    with SessionLocal() as db:
        persisted_price = db.scalar(
            select(FantasyAssetPrice).where(
                FantasyAssetPrice.season == 2026,
                FantasyAssetPrice.round == 2,
            )
        )
        assert persisted_price is not None


def test_lineup_submission_and_audit_persisted():
    payload = {
        "user_id": "local-user",
        "season": 2026,
        "round": 2,
        "drivers": [6, 7, 8, 9, 10],
        "constructors": [104, 105],
        "boost_driver_id": 6,
        "chip": "autopilot",
    }
    submit = client.post("/api/v1/lineups/submit", json=payload)
    assert submit.status_code == 200
    team_id = submit.json()["team_id"]

    current = client.get(
        "/api/v1/lineups/current",
        params={"user_id": "local-user", "season": 2026, "round": 2},
    )
    assert current.status_code == 200
    assert current.json()["team_id"] == team_id

    audit = client.get(
        "/api/v1/audit/lineup",
        params={"user_id": "local-user", "season": 2026, "round": 2},
    )
    assert audit.status_code == 200
    assert len(audit.json()["breakdown"]) > 0

    with SessionLocal() as db:
        team = db.scalar(select(FantasyTeam).where(FantasyTeam.id == team_id))
        ledger = db.scalar(
            select(PointsLedgerEntry).where(
                PointsLedgerEntry.user_id == "local-user",
                PointsLedgerEntry.season == 2026,
                PointsLedgerEntry.round == 2,
                PointsLedgerEntry.team_id == team_id,
            )
        )
        assert team is not None
        assert ledger is not None


def test_transfer_and_chip_history_endpoints():
    user_id = "history-user"

    round_2_payload = {
        "user_id": user_id,
        "season": 2026,
        "round": 2,
        "drivers": [5, 7, 8, 9, 10],
        "constructors": [104, 105],
        "chip": "autopilot",
    }
    round_3_payload = {
        "user_id": user_id,
        "season": 2026,
        "round": 3,
        "drivers": [6, 7, 8, 9, 10],
        "constructors": [104, 105],
        "chip": "triple_boost",
    }

    submit_2 = client.post("/api/v1/lineups/submit", json=round_2_payload)
    assert submit_2.status_code == 200
    submit_3 = client.post("/api/v1/lineups/submit", json=round_3_payload)
    assert submit_3.status_code == 200

    transfers = client.get(
        "/api/v1/lineups/transfers",
        params={"user_id": user_id, "season": 2026, "limit": 10},
    )
    assert transfers.status_code == 200
    transfer_items = transfers.json()["items"]
    assert len(transfer_items) >= 2
    latest = transfer_items[0]
    assert latest["round"] == 3
    assert latest["transfer_count"] == 1
    assert latest["penalty_points"] == 0

    chips = client.get(
        "/api/v1/lineups/chips",
        params={"user_id": user_id, "season": 2026},
    )
    assert chips.status_code == 200
    assert chips.json()["total"] == 2
    assert chips.json()["has_more"] is False
    assert chips.json()["next_offset"] is None
    chip_names = [item["chip"] for item in chips.json()["items"]]
    assert "autopilot" in chip_names
    assert "triple_boost" in chip_names


def test_lineup_history_endpoint_returns_latest_first():
    user_id = "lineup-history-user"

    round_2_payload = {
        "user_id": user_id,
        "season": 2026,
        "round": 2,
        "drivers": [5, 7, 8, 9, 10],
        "constructors": [104, 105],
        "chip": "autopilot",
    }
    round_3_payload = {
        "user_id": user_id,
        "season": 2026,
        "round": 3,
        "drivers": [6, 7, 8, 9, 10],
        "constructors": [104, 105],
        "chip": "triple_boost",
    }

    submit_2 = client.post("/api/v1/lineups/submit", json=round_2_payload)
    assert submit_2.status_code == 200
    submit_3 = client.post("/api/v1/lineups/submit", json=round_3_payload)
    assert submit_3.status_code == 200

    history = client.get(
        "/api/v1/lineups/history",
        params={"user_id": user_id, "season": 2026, "limit": 10},
    )
    assert history.status_code == 200
    items = history.json()["items"]
    assert len(items) >= 2
    assert items[0]["round"] == 3
    assert items[1]["round"] == 2


def test_lineup_by_round_path_endpoint():
    user_id = "lineup-round-user"
    payload = {
        "user_id": user_id,
        "season": 2026,
        "round": 4,
        "drivers": [6, 7, 8, 9, 10],
        "constructors": [104, 105],
    }
    submit = client.post("/api/v1/lineups/submit", json=payload)
    assert submit.status_code == 200

    fetch = client.get(
        "/api/v1/lineups/4",
        params={"user_id": user_id, "season": 2026},
    )
    assert fetch.status_code == 200
    assert fetch.json()["round"] == 4
    assert fetch.json()["user_id"] == user_id


def test_lineup_by_round_path_endpoint_not_found():
    fetch = client.get(
        "/api/v1/lineups/5",
        params={"user_id": "no-lineup-user", "season": 2026},
    )
    assert fetch.status_code == 404


def test_lineup_lifecycle_endpoint_summarizes_round_state():
    user_id = "lifecycle-user"

    round_2_payload = {
        "user_id": user_id,
        "season": 2026,
        "round": 2,
        "drivers": [5, 7, 8, 9, 10],
        "constructors": [104, 105],
        "chip": "autopilot",
    }
    round_3_payload = {
        "user_id": user_id,
        "season": 2026,
        "round": 3,
        "drivers": [6, 7, 8, 9, 10],
        "constructors": [104, 105],
        "chip": "triple_boost",
    }

    submit_2 = client.post("/api/v1/lineups/submit", json=round_2_payload)
    assert submit_2.status_code == 200
    submit_3 = client.post("/api/v1/lineups/submit", json=round_3_payload)
    assert submit_3.status_code == 200

    audit = client.get(
        "/api/v1/audit/lineup",
        params={"user_id": user_id, "season": 2026, "round": 3},
    )
    assert audit.status_code == 200

    lifecycle = client.get(
        "/api/v1/lineups/lifecycle",
        params={"user_id": user_id, "season": 2026, "limit": 10},
    )
    assert lifecycle.status_code == 200

    items = lifecycle.json()["items"]
    assert len(items) >= 2
    assert items[0]["round"] == 3
    assert items[0]["chip"] == "triple_boost"
    assert items[0]["transfer_count"] == 1
    assert items[0]["audited_points"] is not None

    assert items[1]["round"] == 2
    assert items[1]["chip"] == "autopilot"


def test_round_range_filters_on_history_endpoints():
    user_id = "range-filter-user"

    round_2_payload = {
        "user_id": user_id,
        "season": 2026,
        "round": 2,
        "drivers": [5, 7, 8, 9, 10],
        "constructors": [104, 105],
    }
    round_3_payload = {
        "user_id": user_id,
        "season": 2026,
        "round": 3,
        "drivers": [6, 7, 8, 9, 10],
        "constructors": [104, 105],
        "chip": "autopilot",
    }
    round_4_payload = {
        "user_id": user_id,
        "season": 2026,
        "round": 4,
        "drivers": [6, 7, 8, 9, 10],
        "constructors": [104, 105],
        "chip": "triple_boost",
    }

    assert (
        client.post("/api/v1/lineups/submit", json=round_2_payload).status_code == 200
    )
    assert (
        client.post("/api/v1/lineups/submit", json=round_3_payload).status_code == 200
    )
    assert (
        client.post("/api/v1/lineups/submit", json=round_4_payload).status_code == 200
    )

    history = client.get(
        "/api/v1/lineups/history",
        params={
            "user_id": user_id,
            "season": 2026,
            "from_round": 3,
            "to_round": 4,
            "limit": 10,
        },
    )
    assert history.status_code == 200
    assert history.json()["total"] == 2
    assert history.json()["has_more"] is False
    assert history.json()["next_offset"] is None
    history_rounds = [item["round"] for item in history.json()["items"]]
    assert history_rounds == [4, 3]

    transfers = client.get(
        "/api/v1/lineups/transfers",
        params={
            "user_id": user_id,
            "season": 2026,
            "from_round": 3,
            "to_round": 4,
            "limit": 10,
        },
    )
    assert transfers.status_code == 200
    assert transfers.json()["total"] == 2
    assert transfers.json()["has_more"] is False
    assert transfers.json()["next_offset"] is None
    transfer_rounds = [item["round"] for item in transfers.json()["items"]]
    assert transfer_rounds == [4, 3]

    lifecycle = client.get(
        "/api/v1/lineups/lifecycle",
        params={
            "user_id": user_id,
            "season": 2026,
            "from_round": 3,
            "to_round": 4,
            "limit": 10,
        },
    )
    assert lifecycle.status_code == 200
    assert lifecycle.json()["total"] == 2
    assert lifecycle.json()["has_more"] is False
    assert lifecycle.json()["next_offset"] is None
    lifecycle_rounds = [item["round"] for item in lifecycle.json()["items"]]
    assert lifecycle_rounds == [4, 3]


def test_history_pagination_offset_metadata():
    user_id = "pagination-user"

    payloads = [
        {
            "user_id": user_id,
            "season": 2026,
            "round": 2,
            "drivers": [5, 7, 8, 9, 10],
            "constructors": [104, 105],
        },
        {
            "user_id": user_id,
            "season": 2026,
            "round": 3,
            "drivers": [6, 7, 8, 9, 10],
            "constructors": [104, 105],
        },
        {
            "user_id": user_id,
            "season": 2026,
            "round": 4,
            "drivers": [7, 8, 9, 10, 6],
            "constructors": [104, 105],
        },
    ]
    for payload in payloads:
        assert client.post("/api/v1/lineups/submit", json=payload).status_code == 200

    first_page = client.get(
        "/api/v1/lineups/history",
        params={"user_id": user_id, "season": 2026, "limit": 2, "offset": 0},
    )
    assert first_page.status_code == 200
    first_json = first_page.json()
    assert first_json["total"] == 3
    assert first_json["has_more"] is True
    assert first_json["next_offset"] == 2
    assert [item["round"] for item in first_json["items"]] == [4, 3]

    second_page = client.get(
        "/api/v1/lineups/history",
        params={"user_id": user_id, "season": 2026, "limit": 2, "offset": 2},
    )
    assert second_page.status_code == 200
    second_json = second_page.json()
    assert second_json["total"] == 3
    assert second_json["has_more"] is False
    assert second_json["next_offset"] is None
    assert [item["round"] for item in second_json["items"]] == [2]


def test_chip_history_pagination_and_round_filters():
    user_id = "chips-pagination-user"

    assert (
        client.post(
            "/api/v1/lineups/submit",
            json={
                "user_id": user_id,
                "season": 2026,
                "round": 2,
                "drivers": [5, 7, 8, 9, 10],
                "constructors": [104, 105],
                "chip": "autopilot",
            },
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/lineups/submit",
            json={
                "user_id": user_id,
                "season": 2026,
                "round": 3,
                "drivers": [6, 7, 8, 9, 10],
                "constructors": [104, 105],
                "chip": "triple_boost",
            },
        ).status_code
        == 200
    )

    page = client.get(
        "/api/v1/lineups/chips",
        params={
            "user_id": user_id,
            "season": 2026,
            "limit": 1,
            "offset": 0,
            "from_round": 2,
            "to_round": 3,
        },
    )
    assert page.status_code == 200
    body = page.json()
    assert body["total"] == 2
    assert body["has_more"] is True
    assert body["next_offset"] == 1
    assert [item["round"] for item in body["items"]] == [2]

    page_2 = client.get(
        "/api/v1/lineups/chips",
        params={
            "user_id": user_id,
            "season": 2026,
            "limit": 1,
            "offset": 1,
            "from_round": 2,
            "to_round": 3,
        },
    )
    assert page_2.status_code == 200
    body_2 = page_2.json()
    assert body_2["total"] == 2
    assert body_2["has_more"] is False
    assert body_2["next_offset"] is None
    assert [item["round"] for item in body_2["items"]] == [3]


def test_invalid_round_window_returns_400_for_filtered_lineup_endpoints():
    endpoints = [
        "/api/v1/lineups/history",
        "/api/v1/lineups/transfers",
        "/api/v1/lineups/lifecycle",
        "/api/v1/lineups/chips",
    ]

    for endpoint in endpoints:
        response = client.get(
            endpoint,
            params={
                "user_id": "window-validation-user",
                "season": 2026,
                "from_round": 5,
                "to_round": 3,
                "limit": 10,
                "offset": 0,
            },
        )
        assert response.status_code == 400
        body = response.json()
        assert body["error"]["code"] == "invalid_round_window"
        assert (
            body["error"]["message"]
            == "from_round must be less than or equal to to_round"
        )


def test_validation_error_returns_typed_error_envelope():
    response = client.post(
        "/api/v1/simulations/run",
        json={"season": 2026, "round": 2, "n_sims": 0},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "Request validation failed"
    assert isinstance(body["error"]["details"], dict)
    assert isinstance(body["error"]["details"]["issues"], list)


def test_simulation_run_reuses_cached_request_key():
    payload = {"season": 2026, "round": 9, "n_sims": 4321}

    first = client.post("/api/v1/simulations/run", json=payload)
    assert first.status_code == 200
    assert first.headers.get("x-cache") == "MISS"
    first_run_id = first.json()["run_id"]

    second = client.post("/api/v1/simulations/run", json=payload)
    assert second.status_code == 200
    assert second.headers.get("x-cache") == "HIT"
    second_run_id = second.json()["run_id"]

    assert second_run_id == first_run_id

    with SessionLocal() as db:
        run_count = db.scalar(
            select(func.count())
            .select_from(SimulationRun)
            .where(SimulationRun.run_id == first_run_id)
        )
        assert run_count == 1


def test_optimize_is_stable_for_equivalent_used_chip_order():
    base_payload = {
        "season": 2026,
        "round": 3,
        "budget_millions": 100.0,
        "risk_mode": "chip_aware",
        "chip": "autopilot",
    }

    first = client.post(
        "/api/v1/optimize",
        json={**base_payload, "used_chips": ["limitless", "wildcard"]},
    )
    assert first.status_code == 200
    assert first.headers.get("x-cache") == "MISS"

    second = client.post(
        "/api/v1/optimize",
        json={**base_payload, "used_chips": ["wildcard", "limitless"]},
    )
    assert second.status_code == 200
    assert second.headers.get("x-cache") == "HIT"

    assert first.json() == second.json()


def test_cache_invalidate_endpoint_clears_optimizer_namespace():
    payload = {
        "season": 2026,
        "round": 10,
        "budget_millions": 99.9,
        "risk_mode": "max_ev",
        "used_chips": [],
    }

    warm = client.post("/api/v1/optimize", json=payload)
    assert warm.status_code == 200

    invalidate = client.post(
        "/api/v1/cache/invalidate", params={"namespace": "optimizer"}
    )
    assert invalidate.status_code == 200
    body = invalidate.json()
    assert body["namespace"] == "optimizer"
    assert body["deleted"] >= 1

    after = client.post("/api/v1/optimize", json=payload)
    assert after.status_code == 200
    assert after.headers.get("x-cache") == "MISS"
