"""
Application configuration
"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "AI Study Planner"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ai_study_planner"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Ollama AI Service
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TEMPERATURE: float = 0.2
    OLLAMA_NUM_CTX: int = 4096
    OLLAMA_TIMEOUT: int = 30
    
    # AI Service Type (ollama or colab)
    AI_SERVICE_TYPE: str = "ollama"
    
    # Google Colab Configuration (for production)
    COLAB_API_URL: str = ""
    COLAB_API_KEY: str = ""
    
    # LoRA Configuration
    LORA_ENABLED: bool = False
    LORA_ADAPTER_PATH: str = "./lora-adapters"
    LORA_DEFAULT_ADAPTER: str = "study-planning-v1"
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # Resource Limits
    MAX_CONCURRENT_AI_REQUESTS: int = 1
    CACHE_MAX_ENTRIES: int = 100
    CACHE_TTL_SECONDS: int = 300
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Email / SMTP (mot de passe oublié)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@aiplanning.local"
    FRONTEND_URL: str = "http://localhost:5173"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert ALLOWED_ORIGINS string to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()
