"""Pytest suite for the Mergington High School API.

These tests use the Arrange-Act-Assert (AAA) pattern for clarity and a
fixture that snapshots/restores the in-memory `activities` state in
`src.app` between tests to ensure isolation.
"""

import sys
from pathlib import Path

# Ensure the repository root is on sys.path so `from src import app` works
# when running the test file directly (e.g. `python tests/test_app.py`).
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src import app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    snapshot = deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(snapshot)


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_get_activities(client):
    # Arrange: Test client is provided by fixture
    # Act
    r = client.get("/activities")

    # Assert
    assert r.status_code == 200
    data = r.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_success(client):
    # Arrange
    email = "alice@mergington.edu"

    # Act
    r = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert r.status_code == 200
    assert email in app_module.activities["Chess Club"]["participants"]


def test_signup_duplicate(client):
    # Arrange
    email = "dup@test.com"
    r1 = client.post("/activities/Programming%20Class/signup", params={"email": email})
    assert r1.status_code == 200

    # Act
    r2 = client.post("/activities/Programming%20Class/signup", params={"email": email})

    # Assert
    assert r2.status_code == 400
    assert "already signed up" in r2.json()["detail"]


def test_signup_at_capacity(client):
    # Arrange
    name = "Tennis Club"
    activity = app_module.activities[name]
    activity["participants"] = [f"p{i}@x" for i in range(activity["max_participants"])]

    # Act
    r = client.post(f"/activities/{name.replace(' ', '%20')}/signup", params={"email": "capacity@test.com"})

    # Assert
    assert r.status_code == 400
    assert "full" in r.json()["detail"]


def test_remove_participant_success(client):
    # Arrange
    name = "Chess Club"
    email = app_module.activities[name]["participants"][0]

    # Act
    r = client.delete(f"/activities/{name.replace(' ', '%20')}/participants", params={"email": email})

    # Assert
    assert r.status_code == 200
    assert email not in app_module.activities[name]["participants"]


def test_remove_nonexistent_participant(client):
    # Arrange
    email = "noone@x"

    # Act
    r = client.delete("/activities/Chess%20Club/participants", params={"email": email})

    # Assert
    assert r.status_code == 404
