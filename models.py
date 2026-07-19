"""
Pydantic models for API requests and responses.
"""

from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JobStatus(BaseModel):
    """Job status information."""

    job_id: UUID = Field(..., description="Unique job identifier")
    status: Literal["queued", "running", "completed", "failed"] = Field(
        ..., description="Current job status"
    )
    progress: int = Field(
        ..., ge=0, le=100, description="Progress percentage (0-100)"
    )
    total: int = Field(default=0, ge=0, description="Total items to process")
    processed: int = Field(default=0, ge=0, description="Items processed")
    success: int = Field(default=0, ge=0, description="Successfully processed items")
    failed: int = Field(default=0, ge=0, description="Failed items")
    message: str = Field(default="", description="Status message")
    elapsed_time: float = Field(default=0, description="Elapsed time in seconds")
    remaining_time: Optional[float] = Field(
        default=None, description="Estimated remaining time in seconds"
    )
    download_url: Optional[str] = Field(
        default=None, description="Download URL for completed job"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(default=None)


class JobListResponse(BaseModel):
    """Response for listing jobs."""

    jobs: list[JobStatus] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")


class UploadResponse(BaseModel):
    """Response for single image upload."""

    success: bool = Field(..., description="Operation success status")
    output: str = Field(..., description="Output file path")


class UploadCSVResponse(BaseModel):
    """Response for CSV upload."""

    success: bool = Field(..., description="Operation success status")
    job_id: UUID = Field(..., description="Job ID for tracking")
    status: str = Field(..., description="Initial job status")


class DownloadResponse(BaseModel):
    """Response for download endpoint."""

    success: bool = Field(..., description="Operation success status")
    message: Optional[str] = Field(default=None, description="Response message")
    download_url: Optional[str] = Field(default=None, description="Download URL")


class DeleteResponse(BaseModel):
    """Response for delete operation."""

    success: bool = Field(..., description="Operation success status")
    message: Optional[str] = Field(default=None, description="Response message")


class HealthResponse(BaseModel):
    """Response for health check endpoint."""

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = Field(default=False)
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code")
