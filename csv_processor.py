"""
CSV processing module for batch image operations.
Handles downloading images from URLs and processing them in parallel.
"""

import csv
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from uuid import UUID

from config import settings
from downloader import download_images
from image_processor import process_product_image
from job_manager import update_job
from logger import logger


def process_csv(
    csv_file: str,
    output_folder: str,
    canvas_width: int = settings.CANVAS_WIDTH,
    canvas_height: int = settings.CANVAS_HEIGHT,
    scale: int = settings.DEFAULT_SCALE,
    background: tuple[int, int, int] = settings.background_color,
    offset_y: int = 0,
    job_id: Optional[str | UUID] = None,
) -> dict:
    """
    Process CSV file containing product image URLs.

    Args:
        csv_file: Path to CSV file
        output_folder: Output directory for processed images
        canvas_width: Canvas width in pixels
        canvas_height: Canvas height in pixels
        scale: Scale percentage (0-100)
        background: RGB background color tuple
        offset_y: Y-axis offset
        job_id: Job ID for tracking progress

    Returns:
        dict: Processing results
    """
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    temp_folder = Path(tempfile.mkdtemp())
    logger.info(f"Starting CSV processing: {csv_file}")

    processed = 0
    success = 0
    failed = 0
    errors = []

    try:
        # Read CSV and prepare download tasks
        with open(csv_file, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header

            rows = list(reader)
            total = len(rows)

            logger.info(f"Found {total} rows in CSV")

            download_tasks = []

            for row in rows:
                if len(row) < 2:
                    continue

                product_code = row[0].strip()
                urls = [u.strip() for u in row[1:] if u.strip()]

                if not product_code:
                    continue

                for index, url in enumerate(urls, start=1):
                    filename = temp_folder / f"{product_code}-{index}.jpg"
                    download_tasks.append((url, str(filename)))

            if job_id:
                update_job(
                    job_id,
                    status="running",
                    total=total,
                    processed=0,
                    progress=0,
                    success=0,
                    failed=0,
                    message="İşlem başladı. Görseller indiriliyor...",
                )

            # Download all images
            logger.info(f"Downloading {len(download_tasks)} images...")
            download_images(download_tasks, max_workers=settings.MAX_WORKERS)

            # Process downloaded images
            logger.info("Processing downloaded images...")
            for row in rows:
                if len(row) < 2:
                    continue

                product_code = row[0].strip()
                urls = [u.strip() for u in row[1:] if u.strip()]

                if not product_code:
                    continue

                output_dir = output_folder / product_code
                output_dir.mkdir(exist_ok=True)

                for index, url in enumerate(urls, start=1):
                    input_file = temp_folder / f"{product_code}-{index}.jpg"

                    if not input_file.exists():
                        processed += 1
                        failed += 1
                        error_msg = f"Download failed: {url}"
                        errors.append(error_msg)
                        logger.warning(error_msg)

                        if job_id:
                            update_job(
                                job_id,
                                processed=processed,
                                failed=failed,
                                progress=round(processed * 100 / total) if total > 0 else 0,
                                message=error_msg,
                            )
                        continue

                    try:
                        output_file = output_dir / f"{product_code}-{index}.png"

                        process_product_image(
                            input_path=str(input_file),
                            output_path=str(output_file),
                            canvas_width=canvas_width,
                            canvas_height=canvas_height,
                            scale=scale,
                            background=background,
                            offset_y=offset_y,
                        )

                        processed += 1
                        success += 1
                        logger.debug(f"Processed: {product_code}-{index}")

                        if job_id:
                            update_job(
                                job_id,
                                processed=processed,
                                success=success,
                                progress=round(processed * 100 / total) if total > 0 else 0,
                                message=f"{processed}/{total} ürün işlendi.",
                            )
                    except Exception as e:
                        processed += 1
                        failed += 1
                        error_msg = f"{product_code}-{index}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(f"Error processing {product_code}-{index}: {e}")

                        if job_id:
                            update_job(
                                job_id,
                                processed=processed,
                                failed=failed,
                                progress=round(processed * 100 / total) if total > 0 else 0,
                                message=error_msg,
                            )

        if job_id:
            update_job(
                job_id,
                status="completed",
                processed=processed,
                success=success,
                failed=failed,
                progress=100,
                message="Tamamlandı.",
            )

        logger.info(
            f"CSV processing completed. "
            f"Success: {success}, Failed: {failed}, Total: {processed}"
        )

    except Exception as e:
        logger.error(f"Critical error in CSV processing: {e}")
        if job_id:
            update_job(
                job_id,
                status="failed",
                message=f"Kritik hata: {str(e)}",
            )
    finally:
        # Cleanup temp folder
        shutil.rmtree(temp_folder, ignore_errors=True)

    return {
        "success": True,
        "processed": processed,
        "success": success,
        "failed": failed,
        "errors": errors,
    }
