"""
ImgBB image uploader module.
Handles uploading processed images to ImgBB.
"""

import httpx
from pathlib import Path
from typing import Optional

from logger import logger

IMGBB_API_URL = "https://api.imgbb.com/1/upload"


async def upload_image_to_imgbb(
    image_path: str,
    api_key: str,
    timeout: int = 30,
) -> Optional[str]:
    """
    Upload image to ImgBB and return URL.

    Args:
        image_path: Path to image file
        api_key: ImgBB API key
        timeout: Request timeout in seconds

    Returns:
        str: Image URL if successful, None otherwise
    """
    try:
        path = Path(image_path)
        if not path.exists():
            logger.warning(f"Image not found: {image_path}")
            return None

        with open(image_path, "rb") as f:
            files = {"image": f}
            data = {"key": api_key}

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    IMGBB_API_URL,
                    files=files,
                    data=data,
                )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    image_url = result["data"]["url"]
                    logger.info(f"Uploaded to ImgBB: {image_url}")
                    return image_url
                else:
                    logger.error(f"ImgBB error: {result.get('error')}")
                    return None
            else:
                logger.error(f"ImgBB upload failed: {response.status_code}")
                return None

    except Exception as e:
        logger.error(f"Error uploading to ImgBB: {e}")
        return None


def upload_image_to_imgbb_sync(
    image_path: str,
    api_key: str,
    timeout: int = 30,
) -> Optional[str]:
    """
    Synchronous version: Upload image to ImgBB and return URL.

    Args:
        image_path: Path to image file
        api_key: ImgBB API key
        timeout: Request timeout in seconds

    Returns:
        str: Image URL if successful, None otherwise
    """
    try:
        path = Path(image_path)
        if not path.exists():
            logger.warning(f"Image not found: {image_path}")
            return None

        with open(image_path, "rb") as f:
            files = {"image": f}
            data = {"key": api_key}

            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    IMGBB_API_URL,
                    files=files,
                    data=data,
                )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    image_url = result["data"]["url"]
                    logger.info(f"Uploaded to ImgBB: {image_url}")
                    return image_url
                else:
                    logger.error(f"ImgBB error: {result.get('error')}")
                    return None
            else:
                logger.error(f"ImgBB upload failed: {response.status_code}")
                return None

    except Exception as e:
        logger.error(f"Error uploading to ImgBB: {e}")
        return None
