import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app

INITIAL_ACTIVITIES = {
    name: {**data, "participants": list(data["participants"])}
    for name, data in app_module.activities.items()
}


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state after each test."""
    app_module.activities.clear()
    app_module.activities.update(
        {name: {**data, "participants": list(data["participants"])}
         for name, data in INITIAL_ACTIVITIES.items()}
    )
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ── GET /activities ───────────────────────────────────────────────────────────

def test_get_activities_returns_all(client):
    # Arrange — default activities are loaded via fixture

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 9
    assert "Basketball Team" in data
    assert "Soccer Club" in data


def test_get_activities_has_expected_fields(client):
    # Arrange — nothing extra needed

    # Act
    response = client.get("/activities")

    # Assert
    activity = response.json()["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity


# ── POST /activities/{activity_name}/signup ───────────────────────────────────

def test_signup_success(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "a@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate(client):
    # Arrange — michael is already a participant in Chess Club
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


# ── DELETE /activities/{activity_name}/signup ─────────────────────────────────

def test_unregister_success(client):
    # Arrange — michael is already a participant in Chess Club
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "a@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_not_signed_up(client):
    # Arrange
    activity_name = "Chess Club"
    email = "notregistered@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"
