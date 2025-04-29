"""
Delivery Image Module

This module handles the generation and management of delivery images.
"""
import os
import logging
import random
from PIL import Image, ImageDraw, ImageFont

# Configure logging
logger = logging.getLogger(__name__)

# Default image paths
DEFAULT_IMAGE_PATH = "assets/delivery_default.svg"
DELIVERY_IMAGE_PATH = "delivery_custom.jpg"

def create_delivery_image():
    """
    Returns path to a delivery image.
    
    First tries to use a custom image, then falls back to default images,
    and finally generates a new image if needed.
    """
    # Check for custom image first
    if os.path.exists(DELIVERY_IMAGE_PATH) and os.path.getsize(DELIVERY_IMAGE_PATH) > 0:
        logger.info(f"Using custom image: {DELIVERY_IMAGE_PATH}")
        return DELIVERY_IMAGE_PATH
    
    # Use default SVG if it exists
    if os.path.exists(DEFAULT_IMAGE_PATH) and os.path.getsize(DEFAULT_IMAGE_PATH) > 0:
        logger.info(f"Using default image: {DEFAULT_IMAGE_PATH}")
        return DEFAULT_IMAGE_PATH
    
    # Create fallback PNG
    fallback_path = "delivery_fallback.png"
    
    # Use fallback image if it exists
    if os.path.exists(fallback_path) and os.path.getsize(fallback_path) > 0:
        logger.info(f"Using existing fallback image: {fallback_path}")
        return fallback_path
    
    logger.info("Generating new default image")
    
    # Create a new image with a white background
    width, height = 500, 300
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    
    # Get a drawing context
    draw = ImageDraw.Draw(image)
    
    # Draw packages
    draw.rectangle((50, 100, 150, 200), fill=(200, 150, 100), outline=(100, 50, 0), width=3)
    draw.rectangle((200, 120, 300, 220), fill=(150, 200, 100), outline=(50, 100, 0), width=3)
    draw.rectangle((350, 80, 450, 180), fill=(100, 150, 200), outline=(0, 50, 100), width=3)
    
    # Draw delivery truck
    draw.rectangle((50, 40, 200, 80), fill=(255, 0, 0), outline=(0, 0, 0), width=2)  # body
    draw.rectangle((20, 45, 50, 80), fill=(200, 0, 0), outline=(0, 0, 0), width=2)   # cabin
    draw.ellipse((30, 75, 50, 95), fill=(0, 0, 0))  # wheel 1
    draw.ellipse((150, 75, 170, 95), fill=(0, 0, 0))  # wheel 2
    
    # Add text
    try:
        # Try to get a font
        font = ImageFont.load_default()
    except Exception:
        # If font not found, use default
        font = None
    
    draw.text((150, 250), "Доставка посылок", fill=(0, 0, 0), font=font)
    
    # Save the image
    image.save(fallback_path)
    
    return fallback_path
