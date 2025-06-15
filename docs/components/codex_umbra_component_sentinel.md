# Codex Umbra: Component - The Sentinel

## Component Name
The Sentinel

## Role
A distinct Python-based server application representing the internal Master Control Program (MCP) system with which the user, through Codex Umbra, will interact. It exposes an API for control and data retrieval, managed by The Conductor.

## Technology
- Python
- FastAPI (web framework)

## Basic Setup
- Mirrors The Conductor's setup: FastAPI instance and endpoint definitions specific to MCP functionality.
- Example (`mcp_server/main.py`):
  ```python
  from fastapi import FastAPI
  mcp_app = FastAPI(title="The Sentinel MCP")

  @mcp_app.get("/status")
  async def get_status():
      return {"status": "MCP Operational", "version": "1.0.0"}

  # Define other MCP-specific endpoints
  ```

## Project Structure Recommendation
- Similar modular structure to The Conductor:
  ```
  mcp_server_project/
  ├── mcp_server/
  │   ├── main.py
  │   ├── core/
  │   ├── routers/
  │   │   └── control_router.py
  │   ├── services/
  │   │   └── system_service.py
  │   ├── models/             # If database interaction is needed
  │   └── schemas/
  ├── tests/
  └── requirements.txt
  ```

## Health Check Endpoint
- **Path:** `/health`
- **Method:** GET
- **Success Response (HTTP 200 OK):**
  ```json
  {
    "status": "healthy",
    "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
    "version": "1.0.0",
    "dependencies": {
      "database": "connected",
      "external_service": "available"
    }
  }
  ```
- **Failure Response (e.g., HTTP 503 Service Unavailable):**
  ```json
  {
    "status": "unhealthy",
    "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
    "reason": "Database connection failed",
    "details": {}
  }
  ```
- **Usage Example (curl):** `curl -X GET http://localhost:MCP_PORT/health`
