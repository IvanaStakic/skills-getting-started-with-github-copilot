"""
Test suite for Mergington High School Management System API

This module contains unit tests for the FastAPI application endpoints
using the AAA (Arrange-Act-Assert) testing pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Fixture that provides a test client for the FastAPI application.
    This allows us to make requests to the API without running a live server.
    """
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture that resets activities to their initial state before each test.
    This ensures test isolation and prevents tests from affecting each other.
    """
    initial_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        }
    }
    # Arrange: Store original state
    original_state = activities.copy()
    activities.clear()
    activities.update(initial_activities)
    
    yield
    
    # Cleanup: Restore original state
    activities.clear()
    activities.update(original_state)


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that the endpoint returns all available activities"""
        # Arrange: Test client is ready (no setup needed)
        
        # Act: Make request to get activities
        response = client.get("/activities")
        
        # Assert: Verify response status and content
        assert response.status_code == 200
        assert "Chess Club" in response.json()
        assert "Programming Class" in response.json()
        assert len(response.json()) == 2
    
    def test_get_activities_returns_activity_details(self, client, reset_activities):
        """Test that activity details are correctly returned"""
        # Arrange: Test client is ready
        
        # Act: Get activities
        response = client.get("/activities")
        data = response.json()
        
        # Assert: Verify activity structure contains expected fields
        chess_club = data["Chess Club"]
        assert chess_club["description"] == "Learn strategies and compete in chess tournaments"
        assert chess_club["max_participants"] == 12
        assert "michael@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client, reset_activities):
        """Test successful signup for an activity"""
        # Arrange: Prepare request parameters
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act: Send signup request
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert: Verify signup was successful
        assert response.status_code == 200
        assert email in activities["Chess Club"]["participants"]
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    
    def test_signup_to_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that signing up for a non-existent activity returns 404"""
        # Arrange: Define a non-existent activity
        nonexistent_activity = "Underwater Basket Weaving"
        email = "student@mergington.edu"
        
        # Act: Attempt to sign up for non-existent activity
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify 404 error is returned
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_duplicate_raises_error(self, client, reset_activities):
        """Test that signing up twice with the same email raises 400 error"""
        # Arrange: An initial participant is already in Chess Club
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # Act: Attempt to sign up an existing participant
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert: Verify 400 error for duplicate signup
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/unregister endpoint"""
    
    def test_unregister_successful(self, client, reset_activities):
        """Test successful unregistration from an activity"""
        # Arrange: Participant exists in Chess Club
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        assert email in activities[activity_name]["participants"]
        
        # Act: Send unregister request
        response = client.delete(
            "/activities/unregister",
            params={"activity": activity_name, "email": email}
        )
        
        # Assert: Verify unregistration was successful
        assert response.status_code == 200
        assert email not in activities[activity_name]["participants"]
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    
    def test_unregister_from_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that unregistering from non-existent activity returns 404"""
        # Arrange: Define non-existent activity
        nonexistent_activity = "Basket Weaving"
        email = "student@mergington.edu"
        
        # Act: Attempt to unregister from non-existent activity
        response = client.delete(
            "/activities/unregister",
            params={"activity": nonexistent_activity, "email": email}
        )
        
        # Assert: Verify 404 error
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_nonparticipant_returns_404(self, client, reset_activities):
        """Test that unregistering non-participant returns 404"""
        # Arrange: Student not in Programming Class
        activity_name = "Programming Class"
        email = "nonexistent@mergington.edu"
        
        # Act: Attempt to unregister someone not signed up
        response = client.delete(
            "/activities/unregister",
            params={"activity": activity_name, "email": email}
        )
        
        # Assert: Verify 404 error for participant not found
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"
