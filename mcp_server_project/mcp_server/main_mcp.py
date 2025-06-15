"""
The Sentinel - Full MCP Protocol Server Implementation
Replacing the basic REST API with proper Model Context Protocol support
"""

import asyncio
import logging
import uvicorn
from datetime import datetime

from .jsonrpc_server import create_mcp_fastapi_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create the MCP-enabled FastAPI app
mcp_app = create_mcp_fastapi_app()

@mcp_app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🛡️  The Sentinel MCP Server starting up...")
    logger.info("📡 MCP Protocol: JSON-RPC 2.0 with WebSocket/HTTP transport")
    logger.info("🔧 Capabilities: Tools, Resources, Prompts with dynamic discovery")
    logger.info("✅ The Sentinel MCP Server is operational!")

@mcp_app.on_event("shutdown") 
async def shutdown_event():
    """Application shutdown event"""
    logger.info("🛡️  The Sentinel MCP Server shutting down...")
    logger.info("✅ Shutdown complete")

def run_server():
    """Run the MCP server with uvicorn"""
    logger.info("🚀 Launching The Sentinel MCP Server...")
    
    uvicorn.run(
        "mcp_server.main_mcp:mcp_app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    run_server()