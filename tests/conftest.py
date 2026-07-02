import os

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret")

from app import create_app  # noqa: E402
from app.extensions import db as _db  # noqa: E402


@pytest.fixture
def app(tmp_path):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    application = create_app()
    application.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    client.post("/register", data={"username": "ecoUser", "password": "pw123456"})
    client.post("/login", data={"username": "ecoUser", "password": "pw123456"})
    return client
