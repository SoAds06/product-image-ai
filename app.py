"""
Product Image AI - FastAPI Application
Main API endpoints for image processing.
"""

import shutil
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi import FastAPI
from fastapi.responses import FileResponse

from config import settings
from csv_processor import process_csv
from downloader import close_client
from image_processor import process_product_image
from job_manager import create_job, delete_job, get_job, list_jobs, update_job
from logger import logger
from models import (
    DeleteResponse,
    DownloadResponse,
    ErrorResponse,
    HealthResponse,
    JobListResponse,
    JobStatus,
    UploadCSVResponse,
    UploadResponse,
)
from zip_exporter import cleanup_zip, create_zip

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Professional image processing API for product images",
    docs_url="/docs",
    redoc_url="/redoc",
)

logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up resources on shutdown."""
    logger.info("Shutting down application")
    close_client()


@app.get(
    "/",
    response_model=dict,
    tags=["Info"],
    summary="API Information",
)
async def home() -> dict:
    """
    Get API information and status.

    Returns:
        dict: API information
    """
    return {
        "project": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "debug": settings.DEBUG,
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health Check",
)
async def health() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Health status
    """
    return HealthResponse(status="healthy")


@app.post(
    "/upload",
    response_model=UploadResponse,
    tags=["Images"],
    summary="Upload Single Image",
)
async def upload_image(
    file: UploadFile = File(
        ...,
        description="Image file to process",
    ),
    scale: int = Form(
        settings.DEFAULT_SCALE,
        ge=10,
        le=100,
        description="Scale percentage",
    ),
    canvas_width: int = Form(
        settings.CANVAS_WIDTH,
        ge=100,
        description="Canvas width",
    ),
    canvas_height: int = Form(
        settings.CANVAS_HEIGHT,
        ge=100,
        description="Canvas height",
    ),
    offset_y: int = Form(
        0,
        description="Y-axis offset",
    ),
    background_r: int = Form(
        settings.BACKGROUND_R,
        ge=0,
        le=255,
        description="Background red (0-255)",
    ),
    background_g: int = Form(
        settings.BACKGROUND_G,
        ge=0,
        le=255,
        description="Background green (0-255)",
    ),
    background_b: int = Form(
        settings.BACKGROUND_B,
        ge=0,
        le=255,
        description="Background blue (0-255)",
    ),
) -> UploadResponse:
    """
    Upload and process a single image.

    Args:
        file: Image file
        scale: Scale percentage (10-100)
        canvas_width: Canvas width
        canvas_height: Canvas height
        offset_y: Y-axis offset
        background_r: Red channel (0-255)
        background_g: Green channel (0-255)
        background_b: Blue channel (0-255)

    Returns:
        UploadResponse: Processing result

    Raises:
        HTTPException: If processing fails
    """
    try:
        # Save uploaded file
        settings.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        file_path = settings.UPLOAD_FOLDER / file.filename

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        logger.info(f"Processing single image: {file.filename}")

        # Process image
        output_path = settings.OUTPUT_FOLDER / f"{file_path.stem}.png"
        process_product_image(
            input_path=str(file_path),
            output_path=str(output_path),
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            scale=scale,
            background=(background_r, background_g, background_b),
            offset_y=offset_y,
        )

        logger.info(f"Image processed successfully: {output_path}")

        return UploadResponse(success=True, output=str(output_path))

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=400, detail=f"Processing error: {str(e)}")


@app.post(
    "/upload-csv",
    response_model=UploadCSVResponse,
    tags=["Batch Processing"],
    summary="Upload CSV for Batch Processing",
)
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(
        ...,
        description="CSV file with product codes and image URLs",
    ),
    scale: int = Form(
        settings.DEFAULT_SCALE,
        ge=10,
        le=100,
        description="Scale percentage",
    ),
    canvas_width: int = Form(
        settings.CANVAS_WIDTH,
        ge=100,
        description="Canvas width",
    ),
    canvas_height: int = Form(
        settings.CANVAS_HEIGHT,
        ge=100,
        description="Canvas height",
    ),
    offset_y: int = Form(
        0,
        description="Y-axis offset",
    ),
    background_r: int = Form(
        settings.BACKGROUND_R,
        ge=0,
        le=255,
        description="Background red (0-255)",
    ),
    background_g: int = Form(
        settings.BACKGROUND_G,
        ge=0,
        le=255,
        description="Background green (0-255)",
    ),
    background_b: int = Form(
        settings.BACKGROUND_B,
        ge=0,
        le=255,
        description="Background blue (0-255)",
    ),
) -> UploadCSVResponse:
    """
    Upload CSV file for batch processing.

    CSV Format:
        product_code,image_url_1,image_url_2,...

    Args:
        file: CSV file
        scale: Scale percentage (10-100)
        canvas_width: Canvas width
        canvas_height: Canvas height
        offset_y: Y-axis offset
        background_r: Red channel (0-255)
        background_g: Green channel (0-255)
        background_b: Blue channel (0-255)

    Returns:
        UploadCSVResponse: Job information

    Raises:
        HTTPException: If file upload fails
    """
    try:
        # Save CSV file
        settings.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        csv_path = settings.UPLOAD_FOLDER / file.filename

        with open(csv_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Create job
        job_id = create_job()
        logger.info(f"Created batch job: {job_id}")

        # Add background task
        background_tasks.add_task(
            process_csv,
            csv_file=str(csv_path),
            output_folder=str(settings.OUTPUT_FOLDER),
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            scale=scale,
            background=(background_r, background_g, background_b),
            offset_y=offset_y,
            job_id=job_id,
        )

        return UploadCSVResponse(
            success=True,
            job_id=job_id,
            status="queued",
        )

    except Exception as e:
        logger.error(f"Error uploading CSV: {e}")
        raise HTTPException(status_code=400, detail=f"Upload error: {str(e)}")


@app.get(
    "/job/{job_id}",
    response_model=JobStatus,
    tags=["Job Management"],
    summary="Get Job Status",
)
async def job_status(job_id: str) -> JobStatus:
    """
    Get job status and progress.

    Args:
        job_id: Job identifier

    Returns:
        JobStatus: Job information

    Raises:
        HTTPException: If job not found
    """
    job = get_job(job_id)

    if not job:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatus(**job)


@app.get(
    "/jobs",
    response_model=JobListResponse,
    tags=["Job Management"],
    summary="List Jobs",
)
async def jobs_list(
    limit: int = 100,
    offset: int = 0,
) -> JobListResponse:
    """
    List all jobs with pagination.

    Args:
        limit: Maximum number of jobs
        offset: Pagination offset

    Returns:
        JobListResponse: List of jobs
    """
    result = list_jobs(limit=limit, offset=offset)
    return JobListResponse(
        jobs=[JobStatus(**job) for job in result["jobs"]],
        total=result["total"],
    )


@app.get(
    "/download-job/{job_id}",
    tags=["Job Management"],
    summary="Download Job Results",
)
async def download_job(job_id: str) -> FileResponse:
    """
    Download processed images as ZIP.

    Args:
        job_id: Job identifier

    Returns:
        FileResponse: ZIP file

    Raises:
        HTTPException: If job not found
    """
    try:
        folder = settings.OUTPUT_FOLDER / job_id

        if not folder.exists():
            logger.warning(f"Job folder not found: {job_id}")
            raise HTTPException(status_code=404, detail="Job not found")

        logger.info(f"Creating ZIP for job: {job_id}")

        zip_path = settings.OUTPUT_FOLDER / f"{job_id}.zip"
        create_zip(folder, zip_path)

        return FileResponse(
            path=zip_path,
            filename=f"{job_id}.zip",
            media_type="application/zip",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading job {job_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Download error: {str(e)}")


@app.delete(
    "/job/{job_id}",
    response_model=DeleteResponse,
    tags=["Job Management"],
    summary="Delete Job",
)
async def delete_job_endpoint(job_id: str) -> DeleteResponse:
    """
    Delete job and all associated files.

    Args:
        job_id: Job identifier

    Returns:
        DeleteResponse: Deletion status

    Raises:
        HTTPException: If deletion fails
    """
    try:
        logger.info(f"Deleting job: {job_id}")

        # Delete from job manager
        delete_job(job_id)

        # Clean up processed folder
        folder = settings.OUTPUT_FOLDER / job_id
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)

        # Clean up ZIP file
        zip_file = settings.OUTPUT_FOLDER / f"{job_id}.zip"
        cleanup_zip(zip_file)

        logger.info(f"Job deleted successfully: {job_id}")

        return DeleteResponse(success=True)

    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Deletion error: {str(e)}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return ErrorResponse(
        success=False,
        message=exc.detail,
        error_code=f"HTTP_{exc.status_code}",
    )