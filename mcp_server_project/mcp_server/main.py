from fastapi import FastAPI
from datetime import datetime
import uvicorn

mcp_app = FastAPI(
    title="The Sentinel MCP",
    description="Codex Umbra Master Control Program Server",
    version="1.0.0"
)

@mcp_app.get("/")
async def root():
    return {"message": "The Sentinel is operational", "component": "mcp_server"}

@mcp_app.get("/status")
async def get_status():
    return {
        "status": "MCP Operational",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@mcp_app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "dependencies": {
            "system": "available"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:mcp_app", host="0.0.0.0", port=8001, reload=True)