from app.drills_data import get_drills


def test_get_drills_covers_core_skills():
    skills = {d["skill"] for d in get_drills()}
    assert {"Dribbling", "Shooting", "Passing", "Defending", "Fitness"} <= skills
    assert all(d["video_id"] for d in get_drills())


def test_drills_route_renders_videos(auth_client):
    resp = auth_client.get("/drills")
    assert resp.status_code == 200
    assert b"youtube.com/embed/" in resp.data
    assert b"Dribbling" in resp.data
