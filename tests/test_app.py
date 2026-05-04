import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def restore_activities():
    """Restore the in-memory activities dict after each test to prevent state leakage."""
    snapshot = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(snapshot)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self, client):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_dict(self, client):
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_known_activity_present(self, client):
        response = client.get("/activities")
        assert "Chess Club" in response.json()

    def test_activity_has_expected_fields(self, client):
        data = client.get("/activities").json()
        chess = data["Chess Club"]
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_returns_message(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert "message" in response.json()

    def test_unknown_activity_returns_404(self, client):
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404

    def test_already_signed_up_returns_400(self, client):
        # michael is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 400

    def test_full_activity_returns_400(self, client):
        # Fill Chess Club (max 12) — it already has 2 participants
        for i in range(10):
            client.post(
                "/activities/Chess Club/signup",
                params={"email": f"filler{i}@mergington.edu"},
            )
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "overflow@mergington.edu"},
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 200
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_unregister_returns_message(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert "message" in response.json()

    def test_unknown_activity_returns_404(self, client):
        response = client.delete(
            "/activities/Nonexistent Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 404

    def test_participant_not_signed_up_returns_404(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "nobody@mergington.edu"},
        )
        assert response.status_code == 404
