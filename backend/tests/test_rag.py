from fastapi.testclient import TestClient
from app.main import app
from app.storage.db import init_db

init_db()
client = TestClient(app)

def test_query_finance_as_executive():
    # CEO Alice querying finance data
    response = client.get("/api/v1/query?query=What is Q1 2025 revenue?", headers={"x-username": "ceo_alice"})
    assert response.status_code == 200
    data = response.json()
    assert data["routed_intent"] == "SQL_FINANCE"
    assert "response" in data
    assert data["response"]["confidence_score"] > 0.0

def test_query_finance_as_engineer_unauthorized():
    # Lead Bob querying finance data should be blocked by RBAC
    response = client.get("/api/v1/query?query=What is Q1 2025 revenue?", headers={"x-username": "lead_bob"})
    assert response.status_code == 403
    assert "RBAC Policy Violation" in response.json()["detail"]

def test_query_engineering_logs_as_engineer():
    # Lead Bob querying engineering logs
    response = client.get("/api/v1/query?query=Check LDAP SSO commit logs", headers={"x-username": "lead_bob"})
    assert response.status_code == 200
    data = response.json()
    assert data["routed_intent"] in ["SQL_ENGINEERING_LOGS", "UNSTRUCTURED_RAG"]

def test_analytics_dashboard_access():
    # Executive can access analytics
    res1 = client.get("/api/v1/analytics", headers={"x-username": "ceo_alice"})
    assert res1.status_code == 200
    
    # Guest cannot access analytics
    res2 = client.get("/api/v1/analytics", headers={"x-username": "guest_frank"})
    assert res2.status_code == 403
