"""
Module for generating delivery images.
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Paths for delivery images
ASSETS_DIR = 'assets'
OUTPUT_DIR = os.path.join('static', 'images', 'deliveries')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_delivery_image():
    """Returns path to a delivery image."""
    try:
        # Use default delivery background if available
        background_path = os.path.join(ASSETS_DIR, 'delivery_default.svg')
        
        # If SVG not found, look for JPG/PNG backgrounds
        if not os.path.exists(background_path):
            delivery_images = []
            if os.path.exists(ASSETS_DIR):
                delivery_images = [
                    os.path.join(ASSETS_DIR, f) for f in os.listdir(ASSETS_DIR)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg')) and 'delivery' in f.lower()
                ]
            
            # If we found images, pick one randomly
            if delivery_images:
                background_path = random.choice(delivery_images)
            else:
                # Create a simple image with text
                return create_simple_image("Доставка завершена!")
        
        # Create a new file name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f'delivery_{timestamp}.jpg')
        
        # Load and process the image
        try:
            img = Image.open(background_path)
            
            # Resize to a reasonable size
            max_size = (800, 600)
            img.thumbnail(max_size)
            
            # Add text overlay
            draw = ImageDraw.Draw(img)
            
            # Try to load a font, use default if not available
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            
            # Add text
            text = "Доставка завершена!"
            text_width = draw.textlength(text, font=font) if font else 200
            
            # Position text at the bottom center
            position = ((img.width - text_width) // 2, img.height - 50)
            
            # Draw text with shadow for visibility
            draw.text((position[0]+2, position[1]+2), text, font=font, fill=(0, 0, 0))
            draw.text(position, text, font=font, fill=(255, 255, 255))
            
            # Save the image
            img.save(output_path)
            
            return output_path
        except Exception as e:
            logger.error(f"Error processing image {background_path}: {e}")
            return create_simple_image("Доставка завершена!")
    
    except Exception as e:
        logger.error(f"Error in create_delivery_image: {e}")
        return create_simple_image("Доставка завершена!")

def create_simple_image(text):
    """Create a simple image with text when no background is available."""
    try:
        # Create a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f'simple_delivery_{timestamp}.jpg')
        
        # Create a new image with a solid background
        width, height = 600, 400
        img = Image.new('RGB', (width, height), color=(53, 57, 68))
        
        # Add text
        draw = ImageDraw.Draw(img)
        
        # Try to load a font, use default if not available
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        
        # Draw text
        text_width = draw.textlength(text, font=font) if font else 200
        position = ((width - text_width) // 2, height // 2)
        
        # Draw with a white color
        draw.text(position, text, font=font, fill=(255, 255, 255))
        
        # Save the image
        img.save(output_path)
        
        return output_path
    except Exception as e:
        logger.error(f"Error creating simple image: {e}")
        return None