"""
The Conductor - Enhanced with Full MCP Integration
Main application with MCP-enabled routing and dynamic tool discovery
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime

# Import the enhanced MCP router
from app.routers.interaction_router_v2 import router as enhanced_router
# Keep legacy router for backward compatibility
from app.routers.interaction_router import router as legacy_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app with MCP capabilities
app = FastAPI(
    title="The Conductor - MCP Enhanced",
    description="Codex Umbra Backend Orchestrator with Model Context Protocol integration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the enhanced MCP router
app.include_router(enhanced_router, tags=["mcp-enhanced"])

# Include legacy router with different prefix for backward compatibility
app.include_router(legacy_router, prefix="/legacy", tags=["legacy"])

@app.get("/")
async def root():
    """Root endpoint with MCP capability information"""
    return {
        "message": "The Conductor is operational with MCP integration",
        "component": "conductor",
        "version": "2.0.0", 
        "mcp_enabled": True,
        "features": {
            "dynamic_tool_discovery": True,
            "resource_management": True,
            "prompt_templates": True,
            "intelligent_routing": True,
            "legacy_compatibility": True
        },
        "endpoints": {
            "enhanced_chat": "/api/v1/chat",
            "mcp_capabilities": "/api/v1/mcp/capabilities",
            "direct_tool_access": "/api/v1/mcp/tool/{tool_name}",
            "resource_access": "/api/v1/mcp/resource",
            "legacy_chat": "/legacy/api/v1/chat",
            "legacy_health": "/legacy/api/v1/sentinel/health"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/health")
async def health_check():
    """Enhanced health check with MCP status"""
    try:
        # Import here to avoid circular imports
        from app.services.mcp_service_v2 import MCPServiceV2
        
        mcp_service = MCPServiceV2()
        mcp_capabilities = await mcp_service.discover_capabilities()
        
        return {
            "status": "healthy",
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mcp_integration": {
                "enabled": True,
                "connected": mcp_capabilities.get("connection_status", False),
                "tools_available": len(mcp_capabilities.get("tools", [])),
                "resources_available": len(mcp_capabilities.get("resources", [])),
                "prompts_available": len(mcp_capabilities.get("prompts", []))
            },
            "dependencies": {
                "sentinel_mcp": "operational" if mcp_capabilities.get("connection_status") else "unavailable",
                "oracle_llm": "status_unknown"
            }
        }
    except Exception as e:
        logger.warning(f"⚠️  Health check MCP integration failed: {e}")
        return {
            "status": "healthy",
            "version": "2.0.0", 
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mcp_integration": {
                "enabled": True,
                "connected": False,
                "error": str(e)
            },
            "dependencies": {
                "sentinel_mcp": "unavailable",
                "oracle_llm": "status_unknown"
            }
        }

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🎯 The Conductor MCP-Enhanced starting up...")
    logger.info("🔗 MCP Integration: Enabled with dynamic tool discovery")
    logger.info("🛠️  Features: Tool discovery, Resource management, Prompt templates")
    logger.info("🔄 Compatibility: Legacy endpoints available at /legacy/*")
    logger.info("✅ The Conductor MCP-Enhanced is operational!")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("🎯 The Conductor MCP-Enhanced shutting down...")
    
    # Cleanup MCP connections
    try:
        from app.services.mcp_service_v2 import MCPServiceV2
        mcp_service = MCPServiceV2()
        await mcp_service.disconnect()
        logger.info("🔌 MCP connections cleaned up")
    except Exception as e:
        logger.warning(f"⚠️  MCP cleanup warning: {e}")
    
    logger.info("✅ Shutdown complete")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Launching The Conductor MCP-Enhanced...")
    
    uvicorn.run(
        "app.main_mcp:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )