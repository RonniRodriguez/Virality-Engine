"""
Idea Inc - Configuration Management

Centralized configuration using Pydantic Settings.
Supports environment variables and .env files.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ==========================================================================
    # Application
    # ==========================================================================
    app_name: str = "Idea Inc"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", alias="ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    
    # ==========================================================================
    # Server
    # ==========================================================================
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # ==========================================================================
    # Security
    # ==========================================================================
    secret_key: str = Field(
        default="CHANGE-THIS-IN-PRODUCTION-use-openssl-rand-hex-32",
        alias="SECRET_KEY"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        alias="CORS_ORIGINS"
    )
    
    # ==========================================================================
    # OAuth2 Providers
    # ==========================================================================
    # Google
    google_client_id: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/auth/callback/google",
        alias="GOOGLE_REDIRECT_URI"
    )
    
    # GitHub
    github_client_id: Optional[str] = Field(default=None, alias="GITHUB_CLIENT_ID")
    github_client_secret: Optional[str] = Field(default=None, alias="GITHUB_CLIENT_SECRET")
    github_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/auth/callback/github",
        alias="GITHUB_REDIRECT_URI"
    )
    
    # ==========================================================================
    # Database - PostgreSQL
    # ==========================================================================
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="ideainc", alias="POSTGRES_USER")
    postgres_password: str = Field(default="ideainc", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="ideainc", alias="POSTGRES_DB")
    postgres_use_ssl: bool = Field(default=False, alias="POSTGRES_SSL")
    
    @property
    def postgres_url(self) -> str:
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def postgres_url_sync(self) -> str:
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        ssl_suffix = "?sslmode=require" if self.postgres_use_ssl else ""
        return (
            f"postgresql://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}{ssl_suffix}"
        )
    
    # ==========================================================================
    # Database - MongoDB
    # ==========================================================================
    mongodb_host: str = Field(default="localhost", alias="MONGODB_HOST")
    mongodb_port: int = Field(default=27017, alias="MONGODB_PORT")
    mongodb_user: Optional[str] = Field(default=None, alias="MONGODB_USER")
    mongodb_password: Optional[str] = Field(default=None, alias="MONGODB_PASSWORD")
    mongodb_db: str = Field(default="ideainc", alias="MONGODB_DB")
    
    @property
    def mongodb_url(self) -> str:
        if self.mongodb_user and self.mongodb_password:
            return (
                f"mongodb://{self.mongodb_user}:{self.mongodb_password}"
                f"@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_db}"
            )
        return f"mongodb://{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_db}"
    
    # ==========================================================================
    # Cache - Redis
    # ==========================================================================
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # ==========================================================================
    # Event Bus - Kafka
    # ==========================================================================
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        alias="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_consumer_group: str = Field(default="ideainc", alias="KAFKA_CONSUMER_GROUP")
    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    
    # ==========================================================================
    # Vector Database - ChromaDB
    # ==========================================================================
    chroma_host: str = Field(default="localhost", alias="CHROMA_HOST")
    chroma_port: int = Field(default=8001, alias="CHROMA_PORT")
    chroma_persist_directory: str = Field(
        default="./data/chroma",
        alias="CHROMA_PERSIST_DIR"
    )
    
    # ==========================================================================
    # AI / LLM
    # ==========================================================================
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", alias="OPENAI_MODEL")
    llm_enabled: bool = Field(default=False, alias="LLM_ENABLED")
    
    # ==========================================================================
    # Observability
    # ==========================================================================
    # OpenTelemetry
    otel_enabled: bool = Field(default=False, alias="OTEL_ENABLED")
    otel_service_name: str = Field(default="ideainc", alias="OTEL_SERVICE_NAME")
    otel_exporter_endpoint: str = Field(
        default="http://localhost:4317",
        alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    
    # Prometheus
    metrics_enabled: bool = Field(default=True, alias="METRICS_ENABLED")
    metrics_port: int = Field(default=9090, alias="METRICS_PORT")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")  # json or text
    
    # ==========================================================================
    # Simulation
    # ==========================================================================
    default_population_size: int = Field(default=10000, alias="DEFAULT_POPULATION_SIZE")
    simulation_tick_ms: int = Field(default=100, alias="SIMULATION_TICK_MS")
    max_concurrent_worlds: int = Field(default=10, alias="MAX_CONCURRENT_WORLDS")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

