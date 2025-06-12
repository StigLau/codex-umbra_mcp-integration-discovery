import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class MCPService:
    def __init__(self):
        self.base_url = settings.sentinel_url
        self.timeout = 5.0

    async def health_check(self) -> Dict[str, Any]:
        """Check if The Sentinel is healthy and operational."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"status": "unhealthy", "error": f"Connection failed: {str(e)}"}
            except httpx.HTTPStatusError as e:
                return {"status": "unhealthy", "error": f"HTTP {e.response.status_code}"}

    async def get_status(self) -> Dict[str, Any]:
        """Get The Sentinel's operational status."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/status")
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"error": f"Connection failed: {str(e)}"}
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP {e.response.status_code}"}

    async def execute_command(self, command: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a command on The Sentinel (placeholder for future endpoints)."""
        # This is a placeholder for future MCP-specific endpoints
        # For now, return a mock response based on the command
        if command == "get_status":
            return await self.get_status()
        elif command == "health_check":
            return await self.health_check()
        else:
            return {
                "error": f"Unknown command: {command}",
                "available_commands": ["get_status", "health_check"]
            }