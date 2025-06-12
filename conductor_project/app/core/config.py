from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "The Conductor"
    debug: bool = False
    sentinel_url: str = "http://localhost:8001"
    ollama_url: str = "http://localhost:11434"
    
    class Config:
        env_file = ".env"

settings = Settings()