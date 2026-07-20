"""
Configuration module for Product Image AI application.
Manages environment variables and application settings.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # Application
    APP_NAME: str = Field(default="Product Image AI", env="APP_NAME")
    APP_VERSION: str = Field(default="3.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", env="LOG_LEVEL"
    )

    # Paths
    UPLOAD_FOLDER: Path = Field(default=Path("uploads"), env="UPLOAD_FOLDER")
    OUTPUT_FOLDER: Path = Field(default=Path("processed"), env="OUTPUT_FOLDER")
    TEMP_FOLDER: Path = Field(default=Path("/tmp/product-image-ai"), env="TEMP_FOLDER")

    # Canvas settings
    CANVAS_WIDTH: int = Field(default=1200, env="CANVAS_WIDTH")
    CANVAS_HEIGHT: int = Field(default=1500, env="CANVAS_HEIGHT")
    DEFAULT_SCALE: int = Field(default=92, env="DEFAULT_SCALE")
    IMAGE_QUALITY: int = Field(default=85, env="IMAGE_QUALITY", ge=10, le=100)
    BACKGROUND_R: int = Field(default=236, env="BACKGROUND_R", ge=0, le=255)
    BACKGROUND_G: int = Field(default=236, env="BACKGROUND_G", ge=0, le=255)
    BACKGROUND_B: int = Field(default=236, env="BACKGROUND_B", ge=0, le=255)

    # Processing
    MAX_WORKERS: int = Field(default=20, env="MAX_WORKERS", ge=1, le=32)
    MODEL_NAME: str = Field(default="birefnet-general", env="MODEL_NAME")
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT", ge=5)
    DOWNLOAD_CHUNK_SIZE: int = Field(default=8192, env="DOWNLOAD_CHUNK_SIZE", ge=1024)

    # Job management
    JOB_RETENTION_DAYS: int = Field(default=7, env="JOB_RETENTION_DAYS", ge=1)
    MAX_RETRIES: int = Field(default=3, env="MAX_RETRIES", ge=1, le=5)

    # Feature flags
    ENABLE_GPU: bool = Field(default=True, env="ENABLE_GPU")
    CLEANUP_ON_DELETE: bool = Field(default=True, env="CLEANUP_ON_DELETE")

    # ImgBB Configuration
    IMGBB_API_KEY: str = Field(default="", env="IMGBB_API_KEY")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True

    @property
    def background_color(self) -> tuple[int, int, int]:
        """Return background color as RGB tuple."""
        return (self.BACKGROUND_R, self.BACKGROUND_G, self.BACKGROUND_B)

    def model_post_init(self, __context) -> None:
        """Ensure required directories exist."""
        for path in [self.UPLOAD_FOLDER, self.OUTPUT_FOLDER, self.TEMP_FOLDER]:
            path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
