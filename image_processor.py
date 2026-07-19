"""
Image processing module for product image optimization.
Handles background removal, cropping, resizing, and compositing.
"""

from io import BytesIO
from pathlib import Path
from typing import Optional, Union

from PIL import Image
from rembg import remove, new_session

from config import settings
from logger import logger

# Disable DecompressionBomb warning
Image.MAX_IMAGE_PIXELS = None

# Load BiRefNet model once at module load
logger.info(f"Loading BiRefNet model: {settings.MODEL_NAME}")
SESSION = new_session(settings.MODEL_NAME)
logger.info("BiRefNet model loaded successfully")


def remove_background(image: Image.Image) -> Image.Image:
    """
    Remove background from image using BiRefNet.

    Args:
        image: PIL Image object

    Returns:
        Image: Image with transparent background (RGBA)
    """
    try:
        output = remove(image, session=SESSION)

        if isinstance(output, bytes):
            output = Image.open(BytesIO(output)).convert("RGBA")

        return output
    except Exception as e:
        logger.error(f"Error removing background: {e}")
        raise


def crop_transparent_edges(image: Image.Image) -> Image.Image:
    """
    Crop transparent edges from image.

    Args:
        image: PIL Image object

    Returns:
        Image: Cropped image
    """
    bbox = image.getbbox()

    if bbox is None:
        logger.debug("No non-transparent content found, returning original image")
        return image

    logger.debug(f"Cropping image bbox: {bbox}")
    return image.crop(bbox)


def resize_product(
    image: Image.Image,
    canvas_width: int,
    canvas_height: int,
    scale: int,
) -> Image.Image:
    """
    Resize product image to fit canvas with specified scale.

    Args:
        image: PIL Image object
        canvas_width: Canvas width in pixels
        canvas_height: Canvas height in pixels
        scale: Scale percentage (0-100)

    Returns:
        Image: Resized image
    """
    target_width = int(canvas_width * scale / 100)
    target_height = int(canvas_height * scale / 100)

    ratio = min(
        target_width / image.width,
        target_height / image.height,
    )

    new_width = max(1, int(image.width * ratio))
    new_height = max(1, int(image.height * ratio))

    logger.debug(
        f"Resizing image from {image.width}x{image.height} to {new_width}x{new_height}"
    )

    return image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS,
    )


def create_canvas(
    image: Image.Image,
    canvas_width: int,
    canvas_height: int,
    background: tuple[int, int, int],
    offset_y: int = 0,
) -> Image.Image:
    """
    Create canvas and center product image.

    Args:
        image: PIL Image object
        canvas_width: Canvas width in pixels
        canvas_height: Canvas height in pixels
        background: RGB background color tuple
        offset_y: Y-axis offset from center

    Returns:
        Image: Image on canvas
    """
    canvas = Image.new(
        "RGBA",
        (canvas_width, canvas_height),
        background + (255,),
    )

    x = (canvas_width - image.width) // 2
    y = ((canvas_height - image.height) // 2) + offset_y

    canvas.paste(image, (x, y), image)

    logger.debug(f"Created canvas {canvas_width}x{canvas_height} with image at ({x}, {y})")

    return canvas


def process_product_image(
    image: Optional[Image.Image] = None,
    canvas_width: int = settings.CANVAS_WIDTH,
    canvas_height: int = settings.CANVAS_HEIGHT,
    scale: int = settings.DEFAULT_SCALE,
    background: tuple[int, int, int] = settings.background_color,
    offset_y: int = 0,
    input_path: Optional[str | Path] = None,
    output_path: Optional[str | Path] = None,
    remove_bg: bool = True,
    quality: int = settings.IMAGE_QUALITY,
) -> Union[Image.Image, str]:
    """
    Process product image: remove background, crop, resize, and composite.

    Args:
        image: PIL Image object (required if input_path not provided)
        canvas_width: Canvas width in pixels
        canvas_height: Canvas height in pixels
        scale: Scale percentage (0-100)
        background: RGB background color tuple
        offset_y: Y-axis offset from center
        input_path: Path to input image file
        output_path: Path to save output image
        remove_bg: Whether to remove background (default True)
        quality: JPEG quality 10-100 (default 85)

    Returns:
        Image: Processed image (if no output_path)
        str: Path to saved image (if output_path provided)

    Raises:
        ValueError: If neither image nor input_path provided
        Exception: If processing fails
    """
    try:
        # Load image if input_path provided
        if input_path:
            input_file = Path(input_path)
            logger.debug(f"Loading image from {input_file}")
            image = Image.open(input_file).convert("RGBA")
        elif image is None:
            raise ValueError("Either 'image' or 'input_path' must be provided")

        logger.debug("Starting image processing pipeline")

        # Process image
        if remove_bg:
            logger.debug("Removing background with BiRefNet")
            image = remove_background(image)
            image = crop_transparent_edges(image)
        else:
            logger.debug("Skipping background removal")
            image = image.convert("RGBA")

        image = resize_product(image, canvas_width, canvas_height, scale)
        image = create_canvas(image, canvas_width, canvas_height, background, offset_y)

        # Save if output_path provided
        if output_path:
            output_file = Path(output_path)
            # Change extension to .jpg
            output_file = output_file.with_suffix('.jpg')
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert to RGB for JPG (remove alpha channel)
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, settings.background_color)
                rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = rgb_image

            logger.debug(f"Saving image to {output_file}")
            image.save(
                output_file,
                format="JPEG",
                quality=quality,
                optimize=True,
            )
            logger.debug(f"Image saved successfully: {output_file}")
            return str(output_file)

        return image

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise
