import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from PIL import Image


def validate_image_size(value):
    """
    Validate that image file size is within limits.
    
    Args:
        value: ImageField file
    
    Raises:
        ValidationError: If file size exceeds maximum allowed size
    """
    if value:
        # Get max size from settings (default: 5MB)
        max_size = getattr(settings, 'MAX_IMAGE_SIZE', 5 * 1024 * 1024)  # 5MB in bytes
        
        if value.size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            raise ValidationError(
                _('Image file too large. Maximum size is %(max_size)s MB.') % {'max_size': max_size_mb}
            )


def validate_image_format(value):
    """
    Validate that uploaded file is a valid image format.
    
    Args:
        value: ImageField file
    
    Raises:
        ValidationError: If file is not a valid image format
    """
    if value:
        # Get allowed formats from settings
        allowed_formats = getattr(settings, 'ALLOWED_IMAGE_FORMATS', ['JPEG', 'PNG', 'GIF', 'WEBP'])
        
        try:
            # Reset file pointer to beginning
            value.seek(0)
            
            # Open image to verify format
            image = Image.open(value)
            format_name = image.format
            
            if format_name not in allowed_formats:
                raise ValidationError(
                    _('Invalid image format. Allowed formats: %(formats)s.') % {
                        'formats': ', '.join(allowed_formats)
                    }
                )
            
            # Verify it's actually an image by trying to load it
            image.load()
            
            # Reset file pointer after validation
            value.seek(0)
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            # Reset file pointer on error
            try:
                value.seek(0)
            except:
                pass
            raise ValidationError(
                _('Invalid image file. Please upload a valid image.')
            )


def validate_image_dimensions(value):
    """
    Validate that image dimensions are within limits.
    
    Args:
        value: ImageField file
    
    Raises:
        ValidationError: If image dimensions exceed maximum allowed
    """
    if value:
        # Get max dimensions from settings
        max_width = getattr(settings, 'MAX_IMAGE_WIDTH', 4096)
        max_height = getattr(settings, 'MAX_IMAGE_HEIGHT', 4096)
        min_width = getattr(settings, 'MIN_IMAGE_WIDTH', 1)
        min_height = getattr(settings, 'MIN_IMAGE_HEIGHT', 1)
        
        try:
            # Reset file pointer to beginning
            value.seek(0)
            
            image = Image.open(value)
            width, height = image.size
            
            if width > max_width or height > max_height:
                value.seek(0)  # Reset before raising error
                raise ValidationError(
                    _('Image dimensions too large. Maximum size: %(max_width)s x %(max_height)s pixels.') % {
                        'max_width': max_width,
                        'max_height': max_height
                    }
                )
            
            if width < min_width or height < min_height:
                value.seek(0)  # Reset before raising error
                raise ValidationError(
                    _('Image dimensions too small. Minimum size: %(min_width)s x %(min_height)s pixels.') % {
                        'min_width': min_width,
                        'min_height': min_height
                    }
                )
            
            # Reset file pointer after validation
            value.seek(0)
                
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            # Reset file pointer on error
            try:
                value.seek(0)
            except:
                pass
            # If we can't read dimensions, it's not a valid image
            raise ValidationError(
                _('Could not read image dimensions. Please upload a valid image.')
            )

