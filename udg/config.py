"""Configuration management using Pydantic Settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


def _expand_path(path: str) -> Path:
    """Expand ~ to user home directory."""
    return Path(path).expanduser()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    http_port: int = Field(default=8080, validation_alias="UDG_HTTP_PORT")
    grpc_port: int = Field(default=50000, validation_alias="UDG_GRPC_PORT")
    token: Optional[str] = Field(default=None, validation_alias="UDG_TOKEN")
    max_connections: int = Field(default=50, validation_alias="UDG_MAX_CONNECTIONS")
    command_timeout_ms: int = Field(default=60000, validation_alias="UDG_COMMAND_TIMEOUT_MS")
    device_scan_interval: int = Field(default=60, validation_alias="UDG_DEVICE_SCAN_INTERVAL")
    redis_url: Optional[str] = Field(default=None, validation_alias="UDG_REDIS_URL")
    log_level: str = Field(default="INFO", validation_alias="UDG_LOG_LEVEL")
    log_path: Path = Field(default_factory=lambda: _expand_path("~/.udg/logs/udg.log"), validation_alias="UDG_LOG_PATH")
    token_file: Path = Field(default_factory=lambda: _expand_path("~/.udg/token"), validation_alias="UDG_TOKEN_FILE")

    class Config:
        env_file = None
        env_file_encoding = None


settings = Settings()