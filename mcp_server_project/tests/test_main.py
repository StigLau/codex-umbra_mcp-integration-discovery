import pytest
from fastapi.testclient import TestClient
from mcp_server.main import mcp_app

client = TestClient(mcp_app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "The Sentinel is operational"

def test_status():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "MCP Operational"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data
    assert "dependencies" in data