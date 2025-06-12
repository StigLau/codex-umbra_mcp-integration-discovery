import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.services.llm_service import LLMService

@pytest.fixture
def llm_service():
    return LLMService()

@pytest.mark.asyncio
async def test_is_available_success(llm_service):
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value.status_code = 200
        
        result = await llm_service.is_available()
        assert result is True

@pytest.mark.asyncio
async def test_is_available_failure(llm_service):
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.RequestError("Connection failed")
        
        result = await llm_service.is_available()
        assert result is False

@pytest.mark.asyncio
async def test_generate_response_success(llm_service):
    mock_response = {
        "message": {"content": "Test response"},
        "model": "mistral",
        "done": True
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value.status_code = 200
        mock_client.return_value.__aenter__.return_value.post.return_value.json.return_value = mock_response
        
        result = await llm_service.generate_response("Test prompt")
        assert result["response"] == "Test response"
        assert result["model"] == "mistral"
        assert result["done"] is True

@pytest.mark.asyncio
async def test_generate_response_http_error(llm_service):
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value.status_code = 500
        mock_client.return_value.__aenter__.return_value.post.return_value.text = "Server error"
        
        result = await llm_service.generate_response("Test prompt")
        assert "error" in result
        assert "HTTP 500" in result["error"]

@pytest.mark.asyncio
async def test_interpret_user_request(llm_service):
    mock_response = {
        "response": "get_status",
        "model": "mistral",
        "done": True
    }
    
    with patch.object(llm_service, 'generate_response', return_value=mock_response):
        result = await llm_service.interpret_user_request("Check system status")
        assert result["response"] == "get_status"