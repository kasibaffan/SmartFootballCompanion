def test_live_page_shows_start_form_when_no_active_match(auth_client):
    resp = auth_client.get("/live")
    assert resp.status_code == 200
    assert b"Kick Off" in resp.data


def test_start_log_event_and_end_match_flow(auth_client):
    auth_client.post("/live", data={"opponent": "Rivertown FC"})

    events_resp = auth_client.get("/live/events")
    data = events_resp.get_json()
    assert data["active"] is True
    assert data["opponent"] == "Rivertown FC"
    assert data["events"] == []

    event_resp = auth_client.post("/live/event", data={"event_type": "goal"})
    assert event_resp.status_code == 200

    events_resp = auth_client.get("/live/events")
    data = events_resp.get_json()
    assert len(data["events"]) == 1
    assert data["events"][0]["type"] == "goal"

    end_resp = auth_client.post("/live/end")
    assert end_resp.status_code == 302

    events_resp = auth_client.get("/live/events")
    assert events_resp.get_json()["active"] is False


def test_cannot_start_second_active_match(auth_client):
    auth_client.post("/live", data={"opponent": "Team A"})
    auth_client.post("/live", data={"opponent": "Team B"})

    data = auth_client.get("/live/events").get_json()
    assert data["opponent"] == "Team A"


def test_logging_event_without_active_match_returns_error(auth_client):
    resp = auth_client.post("/live/event", data={"event_type": "goal"})
    assert resp.status_code == 400


def test_logging_invalid_event_type_is_rejected(auth_client):
    auth_client.post("/live", data={"opponent": "Team A"})
    resp = auth_client.post("/live/event", data={"event_type": "penalty-shootout"})
    assert resp.status_code == 400


def test_live_routes_require_login(client):
    assert client.get("/live").status_code == 302
    assert client.get("/live/events").status_code == 302
