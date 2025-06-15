import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "The Conductor is operational"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data

@pytest.mark.timeout(10)
def test_chat_endpoint_with_mocked_services():
    with patch("app.services.llm_service.LLMService.is_available", return_value=False), \
         patch("app.services.mcp_service.MCPService.get_status", return_value={"status": "offline"}):
        response = client.post("/api/v1/chat", json={"text": "Hello", "user_id": "test"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "timestamp" in data

@pytest.mark.timeout(10)
def test_chat_endpoint_status_command():
    mock_status_response = {"status": "MCP Operational", "version": "1.0.0"}
    
    with patch("app.services.llm_service.LLMService.is_available", return_value=False), \
         patch("app.services.mcp_service.MCPService.get_status", return_value=mock_status_response):
        
        response = client.post("/api/v1/chat", json={"text": "status", "user_id": "test"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data

@pytest.mark.timeout(10)
def test_sentinel_health_endpoint():
    mock_health_response = {"status": "healthy"}
    
    with patch("app.services.mcp_service.MCPService.health_check", return_value=mock_health_response):
        response = client.get("/api/v1/sentinel/health")
        assert response.status_code == 200
        assert response.json() == mock_health_response