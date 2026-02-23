import uuid

# Global test data
test_data = {
    "email_a": f"user_a_{uuid.uuid4().hex[:8]}@railpulse.com",
    "password_a": "password123",
    "email_b": f"user_b_{uuid.uuid4().hex[:8]}@railpulse.com",
    "password_b": "password456",
}

# --- HELPER FUNCTIONS ---
def setup_user(client, email, password):
    """Helper to register and login a user, returning their Auth header."""
    client.post("/users/register", json={"email": email, "password": password})
    response = client.post("/users/login", data={"username": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def create_test_incident(client, headers, station="LDS"):
    """Helper to quickly create an incident and return its ID."""
    res = client.post("/incidents", headers=headers, json={
        "station_code": station,
        "type": "Crowding",
        "severity": 4,
        "description": "Integration Test Report"
    })
    return res.json()["id"]



def test_register_user_a(client):
    """Test standard registration (User A)."""
    response = client.post("/users/register", json={
        "email": test_data["email_a"],
        "password": test_data["password_a"]
    })
    assert response.status_code == 201
    assert response.json()["email"] == test_data["email_a"]
    assert "id" in response.json()

def test_register_user_b(client):
    """Register second user (User B)."""
    response = client.post("/users/register", json={
        "email": test_data["email_b"],
        "password": test_data["password_b"]
    })
    assert response.status_code == 201

def test_register_duplicate_email(client):
    """Test the API rejects duplicate emails."""
    client.post("/users/register", json={"email": test_data["email_a"], "password": "pass"})
    response = client.post("/users/register", json={"email": test_data["email_a"], "password": "newpassword"})
    assert response.status_code == 400

def test_login_success(client):
    """Test login returns a JWT Token."""
    client.post("/users/register", json={"email": test_data["email_a"], "password": test_data["password_a"]})
    response = client.post("/users/login", data={"username": test_data["email_a"], "password": test_data["password_a"]})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_failure(client):
    """Test login rejects wrong passwords."""
    client.post("/users/register", json={"email": test_data["email_a"], "password": test_data["password_a"]})
    response = client.post("/users/login", data={"username": test_data["email_a"], "password": "WRONG_PASSWORD"})
    assert response.status_code == 401


def test_create_incident_default_station(client):
    """Test User A creating a report using their Token."""
    headers = setup_user(client, test_data["email_a"], test_data["password_a"])
    response = client.post("/incidents", headers=headers, json={
        "train_id": "SERVICE_XYZ_123",
        "type": "Crowding",
        "severity": 4,
        "description": "Integration Test Report"
    })
    assert response.status_code == 201
    assert response.json()["severity"] == 4
    assert response.json()["station_code"] == "LDS"

def test_create_incident_manchester(client):
    """Creating a report for a station."""
    headers = setup_user(client, test_data["email_a"], test_data["password_a"])
    response = client.post("/incidents", headers=headers, json={
        "station_code": "MAN",
        "type": "Crowding",
        "severity": 5,
        "description": "Manchester Chaos"
    })
    assert response.status_code == 201
    assert response.json()["station_code"] == "MAN"

def test_read_my_incidents(client):
    """Test User A seeing their own reports."""
    headers = setup_user(client, test_data["email_a"], test_data["password_a"])
    # Create two incidents
    create_test_incident(client, headers)
    create_test_incident(client, headers)
    
    response = client.get("/incidents/my-reports", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_update_incident_success(client):
    """Test User A updating their own report."""
    headers = setup_user(client, test_data["email_a"], test_data["password_a"])
    incident_id = create_test_incident(client, headers)
    
    response = client.put(f"/incidents/{incident_id}", headers=headers, json={
        "severity": 5,
        "description": "UPDATED: Now very crowded"
    })
    assert response.status_code == 200
    assert response.json()["severity"] == 5


def test_update_incident_unauthorized(client):
    """Test User B can't update User A's report."""
    headers_a = setup_user(client, test_data["email_a"], test_data["password_a"])
    headers_b = setup_user(client, test_data["email_b"], test_data["password_b"])
    
    incident_id = create_test_incident(client, headers_a) # Created by A
    
    response = client.put(f"/incidents/{incident_id}", headers=headers_b, json={"severity": 1}) # B tries to edit
    assert response.status_code == 403

def test_delete_incident_unauthorized(client):
    """Test User B can't delete User A's report."""
    headers_a = setup_user(client, test_data["email_a"], test_data["password_a"])
    headers_b = setup_user(client, test_data["email_b"], test_data["password_b"])
    
    incident_id = create_test_incident(client, headers_a)
    
    response = client.delete(f"/incidents/{incident_id}", headers=headers_b)
    assert response.status_code == 403

def test_access_without_token(client):
    """Test that requests without a token are rejected."""
    response = client.post("/incidents", json={"type": "Delay", "severity": 3})
    assert response.status_code == 401


def test_hub_health_leeds(client):
    """Test the Analytics endpoint"""
    response = client.get("/analytics/LDS/health")
    assert response.status_code == 200
    assert "hub_status" in response.json()

def test_hub_health_station_separation(client):
    """Verify Data Integrity"""
    headers = setup_user(client, test_data["email_a"], test_data["password_a"])
    # Inject a report for Manchester
    create_test_incident(client, headers, station="MAN")
    
    man_response = client.get("/analytics/MAN/health")
    yrk_response = client.get("/analytics/YRK/health")
    
    man_reports = man_response.json()["metrics"]["passenger_reports"]
    yrk_reports = yrk_response.json()["metrics"]["passenger_reports"]
    
    assert man_reports == 1
    assert yrk_reports == 0

def test_live_departures(client):
    """Test fetching trains."""
    response = client.get("/live/departures/KGX")
    assert response.status_code == 200
    assert isinstance(response.json(), list)



def test_delete_incident_success(client):
    """Test User A can delete their own report."""
    headers = setup_user(client, test_data["email_a"], test_data["password_a"])
    incident_id = create_test_incident(client, headers)
    
    response = client.delete(f"/incidents/{incident_id}", headers=headers)
    assert response.status_code == 204

def test_delete_non_existent_incident(client):
    """Test 404 behavior."""
    headers = setup_user(client, test_data["email_a"], test_data["password_a"])
    fake_uuid = str(uuid.uuid4())
    
    response = client.delete(f"/incidents/{fake_uuid}", headers=headers)
    assert response.status_code == 404

def test_validation_missing_fields(client):
    """Test validation."""
    headers = setup_user(client, test_data["email_a"], test_data["password_a"])
    
    response = client.post("/incidents", headers=headers, json={
        "type": "Crowding"
        # Missing severity entirely
    })
    assert response.status_code == 422