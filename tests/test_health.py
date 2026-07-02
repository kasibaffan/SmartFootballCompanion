from app.models import StatEntry


def test_health_route_saves_new_field_set(app, auth_client):
    resp = auth_client.post(
        "/health",
        data={
            "matches": "1", "distance": "8.5", "minutes": "90",
            "challenges": "4", "goals": "2", "assists": "1", "injuries": "0",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        entry = StatEntry.query.first()
        assert entry.distance == 8.5
        assert entry.goals == 2
        assert entry.injuries == 0
        assert not hasattr(entry, "calories")


def test_health_route_rejects_invalid_numbers(auth_client):
    resp = auth_client.post(
        "/health",
        data={
            "matches": "1", "distance": "not-a-number", "minutes": "90",
            "challenges": "4", "goals": "2", "assists": "1", "injuries": "0",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"valid numbers" in resp.data
