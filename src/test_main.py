from fastapi.testclient import TestClient
from main import app
import uuid
import pytest

client = TestClient(app)

# Generate random emails so tests dont fail accidently when run multiple times since we have a unique constraint on email
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
    # Save the ID
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
        "email": test_data["email_a"], # Same as User A
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
# 2. CRUD TESTS (Create, Read, Update, Delete)
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
            "severity": 5, # Escalating severity
            "description": "UPDATED: Now very crowded"
        }
    )
    assert response.status_code == 200
    assert response.json()["severity"] == 5
    assert "UPDATED" in response.json()["description"]



# ==========================================
# 3. AUTHORISATION TESTS
# ==========================================

def test_update_incident_unauthorized():
    """Test that User B CANNOT update User A's report."""
    response = client.put(
        f"/incidents/{test_data['incident_id']}?user_id={test_data['user_id_b']}",
        json={"severity": 1}
    )
    assert response.status_code == 403 # Forbidden

def test_delete_incident_unauthorized():
    """Test that User B CANNOT delete User A's report."""
    response = client.delete(
        f"/incidents/{test_data['incident_id']}?user_id={test_data['user_id_b']}"
    )
    assert response.status_code == 403 # Forbidden

def test_delete_incident_success():
    """Test that User A CAN delete their own report."""
    response = client.delete(
        f"/incidents/{test_data['incident_id']}?user_id={test_data['user_id_a']}"
    )
    assert response.status_code == 204 # No Content

# ==========================================
# 4. ANALYTICS TESTS
# ==========================================

def test_hub_health_structure():
    """
    Test the Innovation Algorithm. 
    This hits the real rail API, so we check if the keys exist 
    rather than specific values (since trains change every minute).
    """
    response = client.get("/analytics/hub-health")
    assert response.status_code == 200
    data = response.json()
    
    # Check that all our complex logic is returning data
    assert "hub_status" in data # GREEN/AMBER/RED
    assert "stress_index" in data
    assert "raw_metrics" in data
    
    # Verify the Score is normalized (0.0 to 1.0)
    score = data["stress_index"]
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0