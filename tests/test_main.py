from fastapi.testclient import TestClient
from src.main import app 
import uuid
import pytest

client = TestClient(app)

# Global storage to share data between tests
test_data = {
    "email_a": f"user_a_{uuid.uuid4().hex[:8]}@leedspulse.com",
    "password_a": "password123",
    "email_b": f"user_b_{uuid.uuid4().hex[:8]}@leedspulse.com",
    "password_b": "password456",
    "incident_id": None
}

def get_auth_header(email, password):
    """Logs in and returns the JWT token header."""
    response = client.post("/users/login", data={
        "username": email, 
        "password": password
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ==========================================
# 1. AUTHENTICATION & SECURITY TESTS
# ==========================================

def test_register_user_a():
    """Test standard registration (User A)."""
    response = client.post("/users/register", json={
        "email": test_data["email_a"],
        "password": test_data["password_a"]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_data["email_a"]
    assert "id" in data

def test_register_user_b():
    """Register a second user (User B) to test RBAC later."""
    response = client.post("/users/register", json={
        "email": test_data["email_b"],
        "password": test_data["password_b"]
    })
    assert response.status_code == 201

def test_register_duplicate_email():
    """Test that the API rejects duplicate emails."""
    response = client.post("/users/register", json={
        "email": test_data["email_a"],
        "password": "newpassword"
    })
    assert response.status_code == 400

def test_login_success():
    """Test login returns a JWT Token (NOT just a user_id)."""
    response = client.post("/users/login", data={
        "username": test_data["email_a"],
        "password": test_data["password_a"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure():
    """Test login rejects wrong passwords."""
    response = client.post("/users/login", data={
        "username": test_data["email_a"],
        "password": "WRONG_PASSWORD"
    })
    assert response.status_code == 401


# ==========================================
# 2. INCIDENT CRUD TESTS (Protected)
# ==========================================

def test_create_incident_default_station():
    """Test User A creating a report using their Token."""
    headers = get_auth_header(test_data["email_a"], test_data["password_a"])
    
    response = client.post(
        "/incidents",
        headers=headers,  # <--- SECURE
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
    test_data["incident_id"] = data["id"]

def test_create_incident_manchester():
    """Test creating a report for a specific station (MAN)."""
    headers = get_auth_header(test_data["email_a"], test_data["password_a"])
    
    response = client.post(
        "/incidents",
        headers=headers,
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
    """Test User A seeing their own reports."""
    headers = get_auth_header(test_data["email_a"], test_data["password_a"])
    
    response = client.get("/incidents/my-reports", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

def test_update_incident_success():
    """Test User A updating their own report."""
    headers = get_auth_header(test_data["email_a"], test_data["password_a"])
    
    response = client.put(
        f"/incidents/{test_data['incident_id']}",
        headers=headers,
        json={
            "severity": 5,
            "description": "UPDATED: Now very crowded"
        }
    )
    assert response.status_code == 200
    assert response.json()["severity"] == 5


# ==========================================
# 3. AUTHORISATION TESTS (RBAC)
# ==========================================

def test_update_incident_unauthorized():
    """Test that User B CANNOT update User A's report."""
    headers_b = get_auth_header(test_data["email_b"], test_data["password_b"])
    
    response = client.put(
        f"/incidents/{test_data['incident_id']}",
        headers=headers_b, # Login as B
        json={"severity": 1}
    )
    assert response.status_code == 403

def test_delete_incident_unauthorized():
    """Test that User B CANNOT delete User A's report."""
    headers_b = get_auth_header(test_data["email_b"], test_data["password_b"])
    
    response = client.delete(
        f"/incidents/{test_data['incident_id']}",
        headers=headers_b
    )
    assert response.status_code == 403

def test_access_without_token():
    """Test that requests without a token are rejected."""
    response = client.post(
        "/incidents",
        json={"type": "Delay", "severity": 3}
    )
    assert response.status_code == 401  # Unauthorized


# ==========================================
# 4. ANALYTICS TESTS (Public)
# ==========================================

def test_hub_health_leeds():
    """Test the Analytics endpoint (Public access allowed)."""
    response = client.get("/analytics/LDS/health")
    assert response.status_code == 200
    data = response.json()
    assert "hub_status" in data

def test_hub_health_station_separation():
    """Verify Data Integrity (Manchester vs Leeds)."""
    # Check Manchester
    man_response = client.get("/analytics/MAN/health")
    man_reports = man_response.json()["metrics"]["passenger_reports"]
    
    # Check York 
    yrk_response = client.get("/analytics/YRK/health")
    yrk_reports = yrk_response.json()["metrics"]["passenger_reports"]
    
    assert man_reports > 0
    if yrk_reports > 0:
        assert man_reports != yrk_reports

def test_live_departures():
    """Test fetching trains."""
    response = client.get("/live/departures/KGX")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ==========================================
# 5. EDGE CASE TESTS
# ==========================================

def test_delete_incident_success():
    """Test that User A CAN delete their own report."""
    headers = get_auth_header(test_data["email_a"], test_data["password_a"])
    
    response = client.delete(
        f"/incidents/{test_data['incident_id']}",
        headers=headers
    )
    assert response.status_code == 204

def test_delete_non_existent_incident():
    """Test 404 behavior."""
    headers = get_auth_header(test_data["email_a"], test_data["password_a"])
    
    response = client.delete(
        f"/incidents/{test_data['incident_id']}",
        headers=headers
    )
    assert response.status_code == 404

def test_validation_missing_fields():
    """Test Pydantic validation."""
    headers = get_auth_header(test_data["email_a"], test_data["password_a"])
    
    response = client.post(
        "/incidents",
        headers=headers,
        json={
            "type": "Crowding"
            # Missing severity
        }
    )
    assert response.status_code == 422