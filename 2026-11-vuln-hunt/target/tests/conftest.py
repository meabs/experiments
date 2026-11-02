import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.seed import seed  # noqa: E402
from shopapi import create_app  # noqa: E402


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db"), "IMAGE_DIR": str(tmp_path / "img"),
                      "CACHE_DIR": str(tmp_path / "cache")})
    seed(app)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email, password="demo-password-1"):
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.get_json()
    return {"Authorization": "Bearer " + r.get_json()["token"]}


@pytest.fixture
def priya(client):
    return login(client, "priya.shah@mail.test")


@pytest.fixture
def staff(client):
    return login(client, "admin@hartleyfinch.co.uk")
