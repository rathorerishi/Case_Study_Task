# Configuration management using Pydantic Settings.
# Loads environment variables and provides typed configuration.

from pydantic_settings import BaseSettings
from pydantic import Field
class Settings(BaseSettings):
    #Application settings loaded from environment variables.
    
    # MongoDB Configuration
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_db_name: str = Field(default="bot_gpt", env="MONGODB_DB_NAME")
    
    # LLM Configuration
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")
    # Context Management
    max_conversation_history: int = Field(default=12, env="MAX_CONVERSATION_HISTORY")
    max_tokens: int = Field(default=7000, env="MAX_TOKENS")
    chunk_size: int = Field(default=600, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, env="CHUNK_OVERLAP")
    
    # Server Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Rate Limiting
    max_requests_per_minute: int = Field(default=60, env="MAX_REQUESTS_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()