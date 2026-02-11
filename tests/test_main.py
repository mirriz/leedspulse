from fastapi.testclient import TestClient
from src.main import app 
import uuid
import pytest

client = TestClient(app)

# Generate random emails so tests dont fail accidently
def get_random_email():
    return f"test_user_{uuid.uuid4().hex[:8]}@leedspulse.com"

# Global storage to share IDs between tests
test_data = {
    "email_a": get_random_email(),
    "email_b": get_random_email(),
    "user_id_a": None,
    "user_id_b": None,
    "incident_id": None
}

# ==========================================
# 1. AUTHENTICATION & SECURITY TESTS
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
# 2. CRUD TESTS
# ==========================================

def test_create_incident():
    """Test that User A can create a report."""
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
    assert data["owner_id"] == test_data["user_id_a"]
    test_data["incident_id"] = data["id"]

def test_read_my_incidents():
    """Test that User A can see their own report."""
    response = client.get(f"/incidents/my-reports?user_id={test_data['user_id_a']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["id"] == test_data["incident_id"]

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

# ==========================================
# 3. AUTHORISATION TESTS
# ==========================================

def test_update_incident_unauthorized():
    """Test that User B CANNOT update User A's report."""
    response = client.put(
        f"/incidents/{test_data['incident_id']}?user_id={test_data['user_id_b']}",
        json={"severity": 1}
    )
    assert response.status_code == 403

def test_delete_incident_unauthorized():
    """Test that User B CANNOT delete User A's report."""
    response = client.delete(
        f"/incidents/{test_data['incident_id']}?user_id={test_data['user_id_b']}"
    )
    assert response.status_code == 403

def test_delete_incident_success():
    """Test that User A CAN delete their own report."""
    response = client.delete(
        f"/incidents/{test_data['incident_id']}?user_id={test_data['user_id_a']}"
    )
    assert response.status_code == 204

# ==========================================
# 4. ANALYTICS TESTS
# ==========================================

def test_hub_health_structure():
    """
    Test the Innovation Algorithm.
    """
    response = client.get("/analytics/hub-health")
    assert response.status_code == 200
    data = response.json()
    
    assert "hub_status" in data
    assert "stress_index" in data
    assert "metrics" in data  # Updated key name from "raw_metrics" to "metrics"
    
    score = data["stress_index"]
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0

# ==========================================
# 5. EDGE CASES & ERROR HANDLING
# ==========================================

def test_login_non_existent_user():
    """Test login with an email that is not in the database."""
    response = client.post("/users/login", json={
        "email": "ghost_user@leedspulse.com",
        "password": "password123"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_create_incident_invalid_user():
    """
    Test creating a report with a random User ID that doesn't exist.
    This ensures referential integrity (Foreign Key checks).
    """
    random_uuid = str(uuid.uuid4())
    response = client.post(
        f"/incidents?user_id={random_uuid}",
        json={
            "type": "Delay",
            "severity": 3,
            "description": "Ghost User Report"
        }
    )
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_update_non_existent_incident():
    """Test updating a report UUID that doesn't exist."""
    random_incident_id = str(uuid.uuid4())
    
    # We use a valid user_id (User A) to pass the first check, 
    # but the incident_id is fake.
    response = client.put(
        f"/incidents/{random_incident_id}?user_id={test_data['user_id_a']}",
        json={"severity": 1}
    )
    assert response.status_code == 404
    assert "Incident not found" in response.json()["detail"]

def test_delete_non_existent_incident():
    """Test deleting a report that has already been deleted or never existed."""
    random_incident_id = str(uuid.uuid4())
    
    response = client.delete(
        f"/incidents/{random_incident_id}?user_id={test_data['user_id_a']}"
    )
    assert response.status_code == 404

def test_validation_missing_fields():
    """
    Test that the API rejects incomplete data (Pydantic Validation).
    Sending a report without 'severity' should fail.
    """
    response = client.post(
        f"/incidents?user_id={test_data['user_id_a']}",
        json={
            "type": "Crowding"
            # Missing 'severity'
        }
    )
    assert response.status_code == 422 # Unprocessable Entity