"""
Image downloader module with connection pooling and retry logic.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import httpx

from config import settings
from logger import logger


# Global HTTP client with connection pool
_client: Optional[httpx.Client] = None


def _get_client() -> httpx.Client:
    """
    Get or create HTTP client with connection pooling.

    Returns:
        httpx.Client: Configured HTTP client
    """
    global _client
    if _client is None:
        _client = httpx.Client(
            timeout=httpx.Timeout(settings.REQUEST_TIMEOUT),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36"
                )
            },
        )
    return _client


def close_client() -> None:
    """Close HTTP client."""
    global _client
    if _client:
        _client.close()
        _client = None


def download_image(
    url: str,
    output_path: str,
    timeout: int = 30,
    retries: int = 3,
) -> bool:
    """
    Download image from URL with retry logic.

    Args:
        url: Image URL
        output_path: Path to save image
        timeout: Request timeout in seconds
        retries: Number of retry attempts

    Returns:
        bool: True if successful, False otherwise
    """
    output_file = Path(output_path)

    for attempt in range(retries):
        try:
            client = _get_client()
            response = client.get(url, timeout=timeout, follow_redirects=True)
            response.raise_for_status()

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=settings.DOWNLOAD_CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)

            logger.debug(f"Downloaded: {url} -> {output_path}")
            return True

        except httpx.HTTPError as e:
            logger.warning(
                f"HTTP error downloading {url} (attempt {attempt + 1}/{retries}): {e}"
            )
            if attempt == retries - 1:
                logger.error(f"Failed to download {url} after {retries} attempts")
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            if output_file.exists():
                output_file.unlink()
            return False

    if output_file.exists():
        output_file.unlink()

    return False


def download_images(
    tasks: list[tuple[str, str]],
    max_workers: int = 8,
) -> list[bool]:
    """
    Download multiple images in parallel with connection pooling.

    Args:
        tasks: List of (url, output_path) tuples
        max_workers: Number of parallel workers

    Returns:
        list[bool]: List of download success status for each task
    """
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_image, url, output): (url, output)
            for url, output in tasks
        }

        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                url, output = futures[future]
                logger.error(f"Exception in download_image({url}): {e}")
                results.append(False)

    return results