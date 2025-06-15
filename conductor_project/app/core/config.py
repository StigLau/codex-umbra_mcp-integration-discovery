from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "The Conductor MCP-Enhanced"
    debug: bool = False
    
    # Legacy Sentinel configuration (for fallback)
    sentinel_url: str = "http://localhost:8001"
    
    # Ollama LLM configuration
    ollama_url: str = "http://localhost:11434"
    
    # MCP Server configuration  
    mcp_host: str = "localhost"
    mcp_port: int = 8001
    mcp_websocket_url: str = None  # Will be auto-generated if not provided
    mcp_http_url: str = None       # Will be auto-generated if not provided
    
    # MCP Client settings
    mcp_connection_timeout: int = 30
    mcp_request_timeout: int = 30
    mcp_auto_reconnect: bool = True
    mcp_discovery_interval: int = 300  # Seconds between capability rediscovery
    
    # Feature flags
    mcp_enhanced_mode: bool = True
    mcp_legacy_fallback: bool = True
    mcp_tool_suggestions: bool = True
    
    class Config:
        env_file = ".env"
    
    def __post_init__(self):
        # Auto-generate MCP URLs if not provided
        if not self.mcp_websocket_url:
            self.mcp_websocket_url = f"ws://{self.mcp_host}:{self.mcp_port}/mcp"
        if not self.mcp_http_url:
            self.mcp_http_url = f"http://{self.mcp_host}:{self.mcp_port}"

settings = Settings()