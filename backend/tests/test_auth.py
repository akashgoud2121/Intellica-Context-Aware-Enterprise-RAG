from fastapi.testclient import TestClient
from app.main import app
from app.storage.db import init_db

init_db()
client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "Operational"

def test_rbac_ceo_access():
    # CEO Alice has Executive role, can access all silos
    response = client.get("/api/v1/auth/users/me", headers={"x-username": "ceo_alice"})
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "Executive"
    assert "finance" in data["allowed_silos"]

def test_rbac_engineering_access():
    # Lead Bob has Engineering role, should not access finance
    response = client.get("/api/v1/auth/users/me", headers={"x-username": "lead_bob"})
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "Engineering"
    assert "finance" not in data["allowed_silos"]

def test_invalid_sso_user():
    response = client.get("/api/v1/auth/users/me", headers={"x-username": "unknown_hacker"})
    assert response.status_code == 401
