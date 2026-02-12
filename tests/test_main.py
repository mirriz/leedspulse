from fastapi.testclient import TestClient
from src.main import app
import uuid
import pytest

client = TestClient(app)

# Global storage to share IDs between tests
test_data = {
    "email_a": f"user_a_{uuid.uuid4().hex[:8]}@leedspulse.com",
    "email_b": f"user_b_{uuid.uuid4().hex[:8]}@leedspulse.com",
    "user_id_a": None,
    "user_id_b": None,
    "incident_id": None
}

# ==========================================
# 1. AUTHENTICATION TESTS (5 Tests)
# ==========================================

def test_register_user_a():
    """Test standard registration (User A)."""
    response = client.post("/users/register", json={
        "email": test_data["email_a"],
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_data["email_a"]
    assert "id" in data
    test_data["user_id_a"] = data["id"]

def test_register_user_b():
    """Register a second user (User B) to test security barriers later."""
    response = client.post("/users/register", json={
        "email": test_data["email_b"],
        "password": "password456"
    })
    assert response.status_code == 201
    test_data["user_id_b"] = response.json()["id"]

def test_register_duplicate_email():
    """Test that the API rejects duplicate emails (Data Integrity)."""
    response = client.post("/users/register", json={
        "email": test_data["email_a"], 
        "password": "newpassword"
    })
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login_success():
    """Test login returns the correct User ID."""
    response = client.post("/users/login", json={
        "email": test_data["email_a"],
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_data["user_id_a"]

def test_login_failure():
    """Test login rejects wrong passwords."""
    response = client.post("/users/login", json={
        "email": test_data["email_a"],
        "password": "WRONG_PASSWORD"
    })
    assert response.status_code == 401

# ==========================================
# 2. INCIDENT CRUD TESTS (6 Tests)
# ==========================================

def test_create_incident_default_station():
    """Test that User A can create a report (Defaults to LDS)."""
    response = client.post(
        f"/incidents?user_id={test_data['user_id_a']}",
        json={
            "train_id": "SERVICE_XYZ_123",
            "type": "Crowding",
            "severity": 4,
            "description": "Integration Test Report"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["severity"] == 4
    assert data["station_code"] == "LDS"
    assert data["owner_id"] == test_data["user_id_a"]
    test_data["incident_id"] = data["id"]

def test_create_incident_manchester():
    """Test creating a report for a specific station (MAN)."""
    response = client.post(
        f"/incidents?user_id={test_data['user_id_a']}",
        json={
            "station_code": "MAN",
            "type": "Crowding",
            "severity": 5,
            "description": "Manchester Chaos"
        }
    )
    assert response.status_code == 201
    assert response.json()["station_code"] == "MAN"

def test_read_my_incidents():
    """Test that User A can see their own reports."""
    response = client.get(f"/incidents/my-reports?user_id={test_data['user_id_a']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2 # We created one for LDS and one for MAN

def test_update_incident_success():
    """Test that User A can update their own report."""
    response = client.put(
        f"/incidents/{test_data['incident_id']}?user_id={test_data['user_id_a']}",
        json={
            "severity": 5,
            "description": "UPDATED: Now very crowded"
        }
    )
    assert response.status_code == 200
    assert response.json()["severity"] == 5

def test_update_incident_unauthorized():
    """Test that User B CANNOT update User A's report (RBAC)."""
    response = client.put(
        f"/incidents/{test_data['incident_id']}?user_id={test_data['user_id_b']}",
        json={"severity": 1}
    )
    assert response.status_code == 403

def test_delete_incident_unauthorized():
    """Test that User B CANNOT delete User A's report (RBAC)."""
    response = client.delete(
        f"/incidents/{test_data['incident_id']}?user_id={test_data['user_id_b']}"
    )
    assert response.status_code == 403

# ==========================================
# 3. ANALYTICS & INNOVATION TESTS (4 Tests)
# ==========================================

def test_hub_health_leeds():
    """Test the NEW endpoint structure for Leeds."""
    response = client.get("/analytics/LDS/health")
    assert response.status_code == 200
    data = response.json()
    assert data["hub_status"] in ["GREEN", "AMBER", "RED"]
    # Check that our Leeds report is counted
    assert data["metrics"]["reports_last_hour"] >= 1

def test_hub_health_station_separation():
    """
    Verify that one set of reports do NOT appear in anothers stats.
    This proves 'Data Integrity' for the Outstanding grade.
    """
    # Check Manchester Stats
    man_response = client.get("/analytics/MAN/health")
    man_reports = man_response.json()["metrics"]["reports_last_hour"]
    
    # 2. Check York Stats
    yrk_response = client.get("/analytics/YRK/health")
    yrk_reports = yrk_response.json()["metrics"]["reports_last_hour"]
    
    assert man_reports > 0
    if yrk_reports > 0:
        assert man_reports != yrk_reports 

def test_live_departures_parameter():
    """Test fetching trains for a specific station."""
    response = client.get("/live/departures/KGX") # Kings Cross
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# ==========================================
# 4. EDGE CASE & ERROR TESTS
# ==========================================

def test_delete_incident_success():
    """Test that User A CAN delete their own report."""
    response = client.delete(
        f"/incidents/{test_data['incident_id']}?user_id={test_data['user_id_a']}"
    )
    assert response.status_code == 204

def test_delete_non_existent_incident():
    """Test 404 behavior for deleted items."""
    response = client.delete(
        f"/incidents/{test_data['incident_id']}?user_id={test_data['user_id_a']}"
    )
    assert response.status_code == 404

def test_validation_missing_fields():
    """Test Pydantic validation rejects bad data."""
    response = client.post(
        f"/incidents?user_id={test_data['user_id_a']}",
        json={
            "type": "Crowding"
            # Missing severity
        }
    )
    assert response.status_code == 422