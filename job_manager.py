"""
Job management system for processing tasks.
Handles job creation, status tracking, and persistence.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional
from uuid import UUID, uuid4

from logger import logger


class Job:
    """
    Represents a processing job with status tracking.
    """

    def __init__(
        self,
        job_id: Optional[UUID] = None,
        status: Literal["queued", "running", "completed", "failed"] = "queued",
        total: int = 0,
        processed: int = 0,
        success: int = 0,
        failed: int = 0,
        message: str = "",
    ) -> None:
        """
        Initialize a Job instance.

        Args:
            job_id: Unique job identifier (auto-generated if not provided)
            status: Current job status
            total: Total items to process
            processed: Number of items processed
            success: Number of successfully processed items
            failed: Number of failed items
            message: Current status message
        """
        self.job_id = job_id or uuid4()
        self.status = status
        self.total = total
        self.processed = processed
        self.success = success
        self.failed = failed
        self.message = message
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.completed_at: Optional[datetime] = None

    @property
    def progress(self) -> int:
        """Calculate progress percentage."""
        if self.total == 0:
            return 0
        return min(100, int(self.processed * 100 / self.total))

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.created_at).total_seconds()

    @property
    def remaining_time(self) -> Optional[float]:
        """Estimate remaining time in seconds."""
        if self.progress == 0 or self.status in ("completed", "failed"):
            return None

        elapsed = self.elapsed_time
        if elapsed == 0:
            return None

        rate = self.progress / elapsed
        if rate == 0:
            return None

        remaining = (100 - self.progress) / rate
        return max(0, remaining)

    def to_dict(self) -> dict:
        """Convert job to dictionary."""
        return {
            "job_id": str(self.job_id),
            "status": self.status,
            "progress": self.progress,
            "total": self.total,
            "processed": self.processed,
            "success": self.success,
            "failed": self.failed,
            "message": self.message,
            "elapsed_time": self.elapsed_time,
            "remaining_time": self.remaining_time,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class JobManager:
    """
    Manages job lifecycle and persistence.
    """

    def __init__(self, storage_path: Path = Path("jobs")) -> None:
        """
        Initialize JobManager.

        Args:
            storage_path: Path to store job data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.jobs: dict[UUID, Job] = {}
        self._load_jobs()

    def create_job(self, job_id: Optional[UUID] = None) -> UUID:
        """
        Create a new job.

        Args:
            job_id: Optional specific job ID

        Returns:
            UUID: Created job ID
        """
        job_id = job_id or uuid4()
        job = Job(job_id=job_id)
        self.jobs[job_id] = job
        self._save_job(job)
        logger.info(f"Created job: {job_id}")
        return job_id

    def get_job(self, job_id: UUID | str) -> Optional[dict]:
        """
        Get job information.

        Args:
            job_id: Job identifier

        Returns:
            dict: Job information or None if not found
        """
        job_id = UUID(job_id) if isinstance(job_id, str) else job_id
        job = self.jobs.get(job_id)
        return job.to_dict() if job else None

    def update_job(
        self,
        job_id: UUID | str,
        status: Optional[Literal["queued", "running", "completed", "failed"]] = None,
        total: Optional[int] = None,
        processed: Optional[int] = None,
        success: Optional[int] = None,
        failed: Optional[int] = None,
        message: Optional[str] = None,
    ) -> bool:
        """
        Update job status.

        Args:
            job_id: Job identifier
            status: New status
            total: Total items
            processed: Items processed
            success: Successful items
            failed: Failed items
            message: Status message

        Returns:
            bool: True if successful
        """
        job_id = UUID(job_id) if isinstance(job_id, str) else job_id
        job = self.jobs.get(job_id)

        if not job:
            logger.warning(f"Job not found: {job_id}")
            return False

        if status:
            job.status = status
        if total is not None:
            job.total = total
        if processed is not None:
            job.processed = processed
        if success is not None:
            job.success = success
        if failed is not None:
            job.failed = failed
        if message is not None:
            job.message = message

        job.updated_at = datetime.now(timezone.utc)

        if status == "completed":
            job.completed_at = datetime.now(timezone.utc)

        self._save_job(job)
        logger.debug(f"Updated job: {job_id} - Status: {status}, Progress: {job.progress}%")
        return True

    def list_jobs(self, limit: int = 100, offset: int = 0) -> dict:
        """
        List all jobs.

        Args:
            limit: Maximum number of jobs to return
            offset: Offset for pagination

        Returns:
            dict: List of jobs and total count
        """
        sorted_jobs = sorted(
            self.jobs.values(),
            key=lambda j: j.created_at,
            reverse=True
        )
        total = len(sorted_jobs)
        jobs = sorted_jobs[offset : offset + limit]

        return {
            "jobs": [job.to_dict() for job in jobs],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def delete_job(self, job_id: UUID | str) -> bool:
        """
        Delete a job.

        Args:
            job_id: Job identifier

        Returns:
            bool: True if successful
        """
        job_id = UUID(job_id) if isinstance(job_id, str) else job_id

        if job_id in self.jobs:
            del self.jobs[job_id]
            self._delete_job_file(job_id)
            logger.info(f"Deleted job: {job_id}")
            return True

        return False

    def _save_job(self, job: Job) -> None:
        """Save job to disk."""
        job_file = self.storage_path / f"{job.job_id}.json"
        try:
            with open(job_file, "w") as f:
                json.dump(job.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save job {job.job_id}: {e}")

    def _delete_job_file(self, job_id: UUID) -> None:
        """Delete job file from disk."""
        job_file = self.storage_path / f"{job_id}.json"
        try:
            if job_file.exists():
                job_file.unlink()
        except Exception as e:
            logger.error(f"Failed to delete job file {job_id}: {e}")

    def _load_jobs(self) -> None:
        """Load jobs from disk."""
        if not self.storage_path.exists():
            return

        for job_file in self.storage_path.glob("*.json"):
            try:
                with open(job_file, "r") as f:
                    data = json.load(f)
                    job = Job(
                        job_id=UUID(data["job_id"]),
                        status=data["status"],
                        total=data["total"],
                        processed=data["processed"],
                        success=data["success"],
                        failed=data["failed"],
                        message=data["message"],
                    )
                    job.created_at = datetime.fromisoformat(data["created_at"])
                    job.updated_at = datetime.fromisoformat(data["updated_at"])
                    if data["completed_at"]:
                        job.completed_at = datetime.fromisoformat(data["completed_at"])
                    self.jobs[job.job_id] = job
            except Exception as e:
                logger.error(f"Failed to load job from {job_file}: {e}")


# Global job manager instance
job_manager = JobManager()


def create_job(job_id: Optional[str | UUID] = None) -> str:
    """Create a new job."""
    if isinstance(job_id, str):
        job_id = UUID(job_id)
    return str(job_manager.create_job(job_id))


def get_job(job_id: str | UUID) -> Optional[dict]:
    """Get job information."""
    return job_manager.get_job(job_id)


def update_job(
    job_id: str | UUID,
    status: Optional[Literal["queued", "running", "completed", "failed"]] = None,
    total: Optional[int] = None,
    processed: Optional[int] = None,
    success: Optional[int] = None,
    failed: Optional[int] = None,
    message: Optional[str] = None,
) -> bool:
    """Update job status."""
    return job_manager.update_job(
        job_id=job_id,
        status=status,
        total=total,
        processed=processed,
        success=success,
        failed=failed,
        message=message,
    )


def list_jobs(limit: int = 100, offset: int = 0) -> dict:
    """List all jobs."""
    return job_manager.list_jobs(limit=limit, offset=offset)


def delete_job(job_id: str | UUID) -> bool:
    """Delete a job."""
    return job_manager.delete_job(job_id)