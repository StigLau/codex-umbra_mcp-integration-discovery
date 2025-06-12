import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.services.mcp_service import MCPService

@pytest.fixture
def mcp_service():
    return MCPService()

@pytest.mark.asyncio
async def test_health_check_success(mcp_service):
    mock_response = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value.json.return_value = mock_response
        mock_client.return_value.__aenter__.return_value.get.return_value.raise_for_status = AsyncMock()
        
        result = await mcp_service.health_check()
        assert result == mock_response

@pytest.mark.asyncio
async def test_health_check_connection_error(mcp_service):
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.RequestError("Connection failed")
        
        result = await mcp_service.health_check()
        assert result["status"] == "unhealthy"
        assert "Connection failed" in result["error"]

@pytest.mark.asyncio
async def test_get_status_success(mcp_service):
    mock_response = {
        "status": "MCP Operational",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value.json.return_value = mock_response
        mock_client.return_value.__aenter__.return_value.get.return_value.raise_for_status = AsyncMock()
        
        result = await mcp_service.get_status()
        assert result == mock_response

@pytest.mark.asyncio
async def test_execute_command_get_status(mcp_service):
    mock_response = {"status": "MCP Operational"}
    
    with patch.object(mcp_service, 'get_status', return_value=mock_response):
        result = await mcp_service.execute_command("get_status")
        assert result == mock_response

@pytest.mark.asyncio
async def test_execute_command_unknown(mcp_service):
    result = await mcp_service.execute_command("unknown_command")
    assert "error" in result
    assert "Unknown command" in result["error"]