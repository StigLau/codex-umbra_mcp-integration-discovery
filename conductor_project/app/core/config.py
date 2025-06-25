from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    app_name: str = "The Conductor MCP-Enhanced"
    debug: bool = False
    environment: str = "development"
    
    # Legacy Sentinel configuration (for fallback)
    sentinel_url: str = "http://localhost:8001"
    
    # LLM Provider Configuration
    default_llm_provider: str = "ollama"  # ollama, anthropic, gemini
    
    # Anthropic Claude Configuration
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_max_tokens: int = 4096
    anthropic_temperature: float = 0.7
    
    # Google Gemini Configuration
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-pro-latest"
    gemini_max_tokens: int = 4096
    gemini_temperature: float = 0.7
    
    # Ollama Configuration (Local LLM)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    ollama_timeout: int = 60
    
    # Service Configuration
    conductor_host: str = "0.0.0.0"
    conductor_port: int = 8000
    conductor_debug: bool = False
    
    # MCP Server configuration  
    mcp_host: str = "localhost"
    mcp_port: int = 8001
    mcp_websocket_url: Optional[str] = None  # Will be auto-generated if not provided
    mcp_http_url: Optional[str] = None       # Will be auto-generated if not provided
    
    # MCP Client settings
    mcp_connection_timeout: int = 30
    mcp_request_timeout: int = 30
    mcp_auto_reconnect: bool = True
    mcp_discovery_interval: int = 300  # Seconds between capability rediscovery
    
    # Feature flags
    mcp_enhanced_mode: bool = True
    mcp_legacy_fallback: bool = True
    mcp_tool_suggestions: bool = True
    
    # Security & Performance
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_size: int = 10
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __post_init__(self):
        # Auto-generate MCP URLs if not provided
        if not self.mcp_websocket_url:
            self.mcp_websocket_url = f"ws://{self.mcp_host}:{self.mcp_port}/mcp"
        if not self.mcp_http_url:
            self.mcp_http_url = f"http://{self.mcp_host}:{self.mcp_port}"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

settings = Settings()