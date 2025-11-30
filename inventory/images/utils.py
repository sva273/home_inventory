import os
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
from PIL import Image
import sys


def resize_image(image_field, max_width=None, max_height=None, quality=85):
    """
    Resize an image while maintaining aspect ratio.
    
    Args:
        image_field: Django ImageField
        max_width: Maximum width in pixels (default from settings)
        max_height: Maximum height in pixels (default from settings)
        quality: JPEG quality (1-100, default: 85)
    
    Returns:
        Resized image as InMemoryUploadedFile or None if no resizing needed
    """
    if not image_field:
        return None
    
    # Get max dimensions from settings if not provided
    if max_width is None:
        from django.conf import settings
        max_width = getattr(settings, 'IMAGE_MAX_WIDTH', 1920)
    
    if max_height is None:
        from django.conf import settings
        max_height = getattr(settings, 'IMAGE_MAX_HEIGHT', 1920)
    
    try:
        # Open the image
        img = Image.open(image_field)
        
        # Convert RGBA to RGB if necessary (for JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get original dimensions
        original_width, original_height = img.size
        
        # Check if resizing is needed
        if original_width <= max_width and original_height <= max_height:
            return None  # No resizing needed
        
        # Calculate new dimensions maintaining aspect ratio
        ratio = min(max_width / original_width, max_height / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        # Resize the image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save to BytesIO
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Create a new InMemoryUploadedFile
        filename = os.path.splitext(image_field.name)[0] + '.jpg'
        content_file = ContentFile(output.read())
        
        return InMemoryUploadedFile(
            content_file,
            'ImageField',
            filename,
            'image/jpeg',
            sys.getsizeof(output),
            None
        )
        
    except Exception as e:
        # Log error but don't fail - return original image
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error resizing image: {str(e)}")
        return None


def optimize_image(image_field, quality=85):
    """
    Optimize image file size without changing dimensions.
    
    Args:
        image_field: Django ImageField
        quality: JPEG quality (1-100, default: 85)
    
    Returns:
        Optimized image as InMemoryUploadedFile or None
    """
    if not image_field:
        return None
    
    try:
        img = Image.open(image_field)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save to BytesIO with optimization
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Check if optimization actually reduced size
        original_size = image_field.size
        optimized_size = sys.getsizeof(output)
        
        if optimized_size >= original_size:
            return None  # Optimization didn't help
        
        # Create a new InMemoryUploadedFile
        filename = os.path.splitext(image_field.name)[0] + '.jpg'
        content_file = ContentFile(output.read())
        
        return InMemoryUploadedFile(
            content_file,
            'ImageField',
            filename,
            'image/jpeg',
            sys.getsizeof(output),
            None
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error optimizing image: {str(e)}")
        return None


def get_image_info(image_field):
    """
    Get information about an image.
    
    Args:
        image_field: Django ImageField
    
    Returns:
        dict with image information (width, height, format, size)
    """
    if not image_field:
        return None
    
    try:
        img = Image.open(image_field)
        return {
            'width': img.size[0],
            'height': img.size[1],
            'format': img.format,
            'mode': img.mode,
            'size': image_field.size,  # File size in bytes
        }
    except Exception:
        return None

