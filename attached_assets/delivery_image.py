"""
Module for generating delivery images.
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Paths for delivery images
ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
OUTPUT_DIR = os.path.join('static', 'images', 'deliveries')

# Ensure directories exist
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Check if we have any delivery background images
def _get_delivery_background():
    """Get a random delivery background image if available."""
    # Check for delivery images in assets directory
    delivery_images = [
        f for f in os.listdir(ASSETS_DIR) 
        if f.lower().endswith(('.png', '.jpg', '.jpeg')) and 'delivery' in f.lower()
    ]
    
    if delivery_images:
        # Return a random image
        return os.path.join(ASSETS_DIR, random.choice(delivery_images))
    
    # Use a fallback image if needed
    return os.path.join(ASSETS_DIR, 'delivery_default.jpg')

def create_delivery_image():
    """Returns path to delivery image."""
    try:
        # Try to get a background image
        background_path = _get_delivery_background()
        
        # If no background is available, just return None for now
        if not os.path.exists(background_path):
            return None
        
        # Create a new image with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f'delivery_{timestamp}.jpg')
        
        # Open the background image
        img = Image.open(background_path)
        
        # Resize to a reasonable size if needed
        max_size = (800, 600)
        img.thumbnail(max_size, Image.LANCZOS)
        
        # Add some text on the image
        draw = ImageDraw.Draw(img)
        
        # Try to load a font, use default if not available
        try:
            font_path = os.path.join(ASSETS_DIR, 'arial.ttf')
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, 30)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Add a delivery completed message
        text = "Доставка завершена!"
        text_width = draw.textlength(text, font=font)
        
        # Position text at the bottom center
        position = ((img.width - text_width) // 2, img.height - 50)
        
        # Draw text with black outline for visibility
        draw.text((position[0]-1, position[1]), text, font=font, fill=(0, 0, 0))
        draw.text((position[0]+1, position[1]), text, font=font, fill=(0, 0, 0))
        draw.text((position[0], position[1]-1), text, font=font, fill=(0, 0, 0))
        draw.text((position[0], position[1]+1), text, font=font, fill=(0, 0, 0))
        
        # Draw actual text in white
        draw.text(position, text, font=font, fill=(255, 255, 255))
        
        # Save the image
        img.save(output_path)
        
        return output_path
    except Exception as e:
        print(f"Error creating delivery image: {e}")
        return None