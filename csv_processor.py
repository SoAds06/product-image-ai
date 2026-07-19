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
from imgbb_uploader import upload_image_to_imgbb_sync
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
    imgbb_api_key: Optional[str] = None,
    remove_background: bool = True,
    quality: int = settings.IMAGE_QUALITY,
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
            total = 0

            logger.info(f"Found {len(rows)} product rows in CSV")

            download_tasks = []
            product_codes = []
            logger.info("Created empty download_tasks list")

            logger.info("Starting loop through rows")
            for row in rows:
                logger.debug(f"Processing row: {row[0] if row else 'empty'}")
                if len(row) < 2:
                    continue

                product_code = row[0].strip()

                # Parse URLs from column 1 (comma-separated format)
                urls_str = row[1].strip() if len(row) > 1 else ""
                urls = [u.strip() for u in urls_str.split(",") if u.strip()]

                if not product_code or not urls:
                    logger.warning(f"Skipping row: product_code={product_code}, urls_count={len(urls)}")
                    continue

                logger.info(f"Product {product_code}: {len(urls)} URLs")
                product_codes.append(product_code)
                total += len(urls)

                for index, url in enumerate(urls, start=1):
                    filename = temp_folder / f"{product_code}-{index}.jpg"
                    download_tasks.append((url, str(filename)))

            if job_id:
                try:
                    logger.info(f"Calling update_job with job_id={job_id}, status=running, total={total}")
                    update_job(
                        job_id,
                        status="running",
                        total=total,
                        processed=0,
                        success=0,
                        failed=0,
                        message="İşlem başladı. Görseller indiriliyor...",
                    )
                    logger.info("update_job call successful")
                except TypeError as e:
                    logger.error(f"TypeError in update_job call: {e}")
                    raise

            # Download all images
            logger.info(f"Downloading {len(download_tasks)} images...")
            download_images(download_tasks, max_workers=settings.MAX_WORKERS)

            # Process downloaded images
            logger.info("Processing downloaded images...")
            for row in rows:
                if len(row) < 2:
                    continue

                product_code = row[0].strip()

                # Parse URLs from column 1 (comma-separated format)
                urls_str = row[1].strip() if len(row) > 1 else ""
                urls = [u.strip() for u in urls_str.split(",") if u.strip()]

                if not product_code or not urls:
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
                                message=error_msg,
                            )
                        continue

                    try:
                        output_file = output_dir / f"{product_code}-{index}.jpg"

                        process_product_image(
                            input_path=str(input_file),
                            output_path=str(output_file),
                            canvas_width=canvas_width,
                            canvas_height=canvas_height,
                            scale=scale,
                            background=background,
                            offset_y=offset_y,
                            remove_bg=remove_background,
                            quality=quality,
                        )

                        processed += 1
                        success += 1
                        logger.debug(f"Processed: {product_code}-{index}")

                        if job_id:
                            update_job(
                                job_id,
                                processed=processed,
                                success=success,
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
                                message=error_msg,
                            )

        # Upload to ImgBB if API key provided
        if imgbb_api_key:
            logger.info("Starting ImgBB upload...")
            if job_id:
                update_job(
                    job_id,
                    message="Görseller ImgBB'ye yükleniyor...",
                )

            create_imgbb_csv(
                output_folder=output_folder,
                imgbb_api_key=imgbb_api_key,
                job_id=job_id,
                product_codes=product_codes,
            )

        if job_id:
            update_job(
                job_id,
                status="completed",
                processed=processed,
                success=success,
                failed=failed,
                message="Tamamlandı.",
            )

        logger.info(
            f"CSV processing completed. "
            f"Success: {success}, Failed: {failed}, Total: {processed}"
        )

    except Exception as e:
        logger.error(f"Critical error in CSV processing: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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


def create_imgbb_csv(
    output_folder: str,
    imgbb_api_key: str,
    job_id: Optional[str | UUID] = None,
    product_codes: Optional[list[str]] = None,
) -> None:
    """
    Upload processed images to ImgBB and create CSV with URLs.

    Args:
        output_folder: Folder containing product folders with processed images
        imgbb_api_key: ImgBB API key
        job_id: Job ID for progress tracking and filename
        product_codes: List of product codes to process (if None, process all)
    """
    try:
        output_path = Path(output_folder)
        csv_data = []

        logger.info("Scanning processed images for ImgBB upload...")

        # Scan product folders
        for product_folder in sorted(output_path.iterdir()):
            if not product_folder.is_dir():
                continue

            product_code = product_folder.name

            # Skip if product_codes list is provided and this product is not in it
            if product_codes and product_code not in product_codes:
                logger.debug(f"Skipping product (not in current batch): {product_code}")
                continue

            logger.info(f"Processing product: {product_code}")

            # Scan images in product folder
            for image_file in sorted(product_folder.glob("*.jpg")):
                logger.info(f"Uploading to ImgBB: {image_file.name}")

                # Upload to ImgBB
                image_url = upload_image_to_imgbb_sync(
                    str(image_file),
                    imgbb_api_key,
                )

                if image_url:
                    csv_data.append([product_code, image_url])
                    logger.info(f"✓ Uploaded: {image_url}")
                else:
                    logger.warning(f"✗ Failed to upload: {image_file.name}")

        # Create CSV with image URLs
        if csv_data:
            csv_filename = f"image_urls_{job_id}.csv" if job_id else "image_urls.csv"
            csv_path = output_path.parent / csv_filename

            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["product_code", "image_url"])
                writer.writerows(csv_data)

            logger.info(f"Created image URL CSV: {csv_path}")
            logger.info(f"Total images uploaded: {len(csv_data)}")
        else:
            logger.warning("No images were uploaded to ImgBB")

    except Exception as e:
        logger.error(f"Error creating ImgBB CSV: {e}")
        if job_id:
            update_job(
                job_id,
                message=f"ImgBB upload hatası: {str(e)}",
            )
