def test_register_and_login(client):
    client.post("/register", data={"username": "alice", "password": "secret123"})
    resp = client.post(
        "/login", data={"username": "alice", "password": "secret123"}, follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"Welcome back, alice" in resp.data


def test_duplicate_username_rejected(client):
    client.post("/register", data={"username": "bob", "password": "pw123456"})
    resp = client.post(
        "/register", data={"username": "bob", "password": "other12345"}, follow_redirects=True
    )
    assert b"already taken" in resp.data


def test_wrong_password_rejected(client):
    client.post("/register", data={"username": "carol", "password": "correct123"})
    resp = client.post(
        "/login", data={"username": "carol", "password": "wrong-password"}, follow_redirects=True
    )
    assert b"Invalid username or password" in resp.data


def test_dashboard_requires_login(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_password_is_hashed_not_plaintext(app, client):
    from app.models import User

    client.post("/register", data={"username": "dave", "password": "plaintextpw"})
    with app.app_context():
        user = User.query.filter_by(username="dave").first()
        assert user.password_hash != "plaintextpw"
        assert user.check_password("plaintextpw")
