"""
ZIP export module for creating compressed archives.
"""

import zipfile
from pathlib import Path

from logger import logger


def create_zip(
    source_folder: str | Path,
    output_zip: str | Path,
) -> str:
    """
    Create ZIP archive from folder contents.

    Args:
        source_folder: Source folder path
        output_zip: Output ZIP file path

    Returns:
        str: Path to created ZIP file

    Raises:
        FileNotFoundError: If source folder doesn't exist
        Exception: If ZIP creation fails
    """
    source_folder = Path(source_folder)
    output_zip = Path(output_zip)

    if not source_folder.exists():
        logger.error(f"Source folder not found: {source_folder}")
        raise FileNotFoundError(f"Source folder not found: {source_folder}")

    try:
        logger.info(f"Creating ZIP archive: {output_zip}")
        output_zip.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(
            output_zip,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
        ) as zipf:
            file_count = 0
            for file_path in source_folder.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_folder)
                    zipf.write(file_path, arcname=arcname)
                    file_count += 1

        logger.info(f"ZIP archive created successfully: {output_zip} ({file_count} files)")
        return str(output_zip)

    except Exception as e:
        logger.error(f"Error creating ZIP archive: {e}")
        # Clean up partial ZIP file
        if output_zip.exists():
            output_zip.unlink()
        raise


def cleanup_zip(zip_path: str | Path) -> bool:
    """
    Delete ZIP file.

    Args:
        zip_path: Path to ZIP file

    Returns:
        bool: True if successful, False otherwise
    """
    zip_path = Path(zip_path)

    try:
        if zip_path.exists():
            zip_path.unlink()
            logger.info(f"Deleted ZIP file: {zip_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting ZIP file {zip_path}: {e}")
        return False
