"""ImageData model for managing image state and metadata."""

from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import datetime

from PIL import Image

from ..utils.exceptions import ValidationError, ImageProcessingError
from ..utils.logger import get_logger
from ..constants import SUPPORTED_IMAGE_TYPES, SUPPORTED_MIME_TYPES

logger = get_logger(__name__)


@dataclass
class ImageData:
    """Manages image data, metadata, and validation."""
    
    original_image: Optional[Image.Image] = None
    processed_image: Optional[Image.Image] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    original_dimensions: Optional[Tuple[int, int]] = None
    processed_dimensions: Optional[Tuple[int, int]] = None
    format: Optional[str] = None
    processing_params: Dict[str, Any] = field(default_factory=dict)
    upload_time: Optional[datetime.datetime] = None
    processing_time: Optional[datetime.datetime] = None
    # Sample image fields
    is_sample: bool = False
    sample_display_name: Optional[str] = None
    
    def __post_init__(self):
        """Initialize metadata after dataclass creation."""
        if self.original_image and not self.original_dimensions:
            self.original_dimensions = self.original_image.size
            logger.info(f"Image dimensions: {self.original_dimensions}")
    
    @classmethod
    def from_uploaded_file(cls, uploaded_file) -> 'ImageData':
        """
        Create ImageData from a Streamlit uploaded file.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            ImageData instance
            
        Raises:
            ValidationError: If file validation fails
            ImageProcessingError: If image processing fails
        """
        if uploaded_file is None:
            raise ValidationError(
                "No file uploaded",
                "Please select an image file to upload."
            )
        
        # Validate file type
        file_extension = Path(uploaded_file.name).suffix.lower().lstrip('.')
        if file_extension not in SUPPORTED_IMAGE_TYPES:
            raise ValidationError(
                f"Unsupported file type: {file_extension}",
                f"Please upload a supported image format: {', '.join(SUPPORTED_IMAGE_TYPES).upper()}"
            )
        
        # Validate MIME type
        if hasattr(uploaded_file, 'type') and uploaded_file.type not in SUPPORTED_MIME_TYPES:
            raise ValidationError(
                f"Unsupported MIME type: {uploaded_file.type}",
                "Please upload a valid image file."
            )
        
        try:
            # Load and validate image
            image = Image.open(uploaded_file).convert("RGB")
            
            # Validate image dimensions
            width, height = image.size
            if width < 100 or height < 100:
                raise ValidationError(
                    f"Image too small: {width}x{height}",
                    "Please upload an image that is at least 100x100 pixels."
                )
            
            if width > 10000 or height > 10000:
                raise ValidationError(
                    f"Image too large: {width}x{height}",
                    "Please upload an image smaller than 10000x10000 pixels."
                )
            
            # Memory optimization: Resize large images for cloud deployment
            original_size = (width, height)
            image = cls._optimize_image_for_memory(image)
            
            logger.info(f"Successfully loaded image: {uploaded_file.name} ({width}x{height})")
            
            return cls(
                original_image=image,
                filename=uploaded_file.name,
                file_size=getattr(uploaded_file, 'size', None),
                original_dimensions=(width, height),
                format=file_extension.upper(),
                upload_time=datetime.datetime.now()
            )
            
        except Exception as e:
            if isinstance(e, (ValidationError, ImageProcessingError)):
                raise
            
            logger.error(f"Failed to process uploaded image: {e}")
            raise ImageProcessingError(
                f"Failed to process image: {e}",
                "Unable to process the uploaded image. Please try a different image."
            )
    
    @classmethod
    def from_sample_image(cls, image_path: str, display_name: str) -> 'ImageData':
        """
        Create ImageData from a sample image file.
        
        Args:
            image_path: Path to the sample image file
            display_name: User-friendly display name for the image
            
        Returns:
            ImageData instance
            
        Raises:
            ValidationError: If file validation fails
            ImageProcessingError: If image processing fails
        """
        try:
            image_path = Path(image_path)
            
            if not image_path.exists():
                raise ValidationError(
                    f"Sample image not found: {image_path}",
                    "The selected sample image is not available."
                )
            
            # Load and validate image
            image = Image.open(image_path).convert("RGB")
            
            # Validate image dimensions
            width, height = image.size
            if width < 100 or height < 100:
                logger.warning(f"Sample image is quite small: {width}x{height}")
            
            # Memory optimization: Resize large images for cloud deployment
            image = cls._optimize_image_for_memory(image)
            
            logger.info(f"Successfully loaded sample image: {display_name} ({width}x{height})")
            
            return cls(
                original_image=image,
                filename=f"sample_{image_path.name}",
                file_size=image_path.stat().st_size,
                original_dimensions=(width, height),
                format=image_path.suffix.upper().lstrip('.'),
                upload_time=datetime.datetime.now(),
                is_sample=True,
                sample_display_name=display_name
            )
            
        except Exception as e:
            if isinstance(e, (ValidationError, ImageProcessingError)):
                raise
            
            logger.error(f"Failed to process sample image {image_path}: {e}")
            raise ImageProcessingError(
                f"Failed to process sample image: {e}",
                "Unable to process the selected sample image. Please try a different one."
            )
    
    def set_processed_image(
        self, 
        processed_image: Image.Image, 
        processing_params: Dict[str, Any]
    ) -> None:
        """
        Set the processed image and its parameters.
        
        Args:
            processed_image: The processed PIL Image
            processing_params: Parameters used for processing
        """
        self.processed_image = processed_image
        self.processed_dimensions = processed_image.size
        self.processing_params = processing_params.copy()
        self.processing_time = datetime.datetime.now()
        
        logger.info(f"Processed image set: {self.processed_dimensions}")
    
    def validate_for_processing(self) -> None:
        """
        Validate that the image data is ready for processing.
        
        Raises:
            ValidationError: If validation fails
        """
        if self.original_image is None:
            raise ValidationError(
                "No original image available",
                "Please upload an image before processing."
            )
        
        if not self.original_dimensions:
            raise ValidationError(
                "No image dimensions available",
                "Image data is corrupted. Please upload the image again."
            )
        
        logger.debug("Image validation passed")
    
    def get_aspect_ratio(self) -> Optional[float]:
        """
        Get the aspect ratio of the original image.
        
        Returns:
            Aspect ratio (width/height) or None if no image
        """
        if not self.original_dimensions:
            return None
        
        width, height = self.original_dimensions
        return width / height if height > 0 else None
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get a summary of processing information.
        
        Returns:
            Dictionary with processing summary
        """
        return {
            "filename": self.filename,
            "original_size": self.original_dimensions,
            "processed_size": self.processed_dimensions,
            "format": self.format,
            "file_size": self.file_size,
            "aspect_ratio": self.get_aspect_ratio(),
            "upload_time": self.upload_time,
            "processing_time": self.processing_time,
            "processing_params": self.processing_params
        }
    
    def clear(self) -> None:
        """Clear all image data."""
        self.original_image = None
        self.processed_image = None
        self.filename = None
        self.file_size = None
        self.original_dimensions = None
        self.processed_dimensions = None
        self.format = None
        self.processing_params = {}
        self.upload_time = None
        self.processing_time = None
        self.is_sample = False
        self.sample_display_name = None
        
        logger.info("Image data cleared")
    
    @staticmethod
    def _optimize_image_for_memory(image: Image.Image, max_dimension: int = 2048) -> Image.Image:
        """
        Optimize image for memory usage by resizing if too large.
        
        Args:
            image: PIL Image to optimize
            max_dimension: Maximum width or height (default: 2048px)
            
        Returns:
            Optimized PIL Image
        """
        width, height = image.size
        original_pixels = width * height
        
        # Only resize if image is larger than max_dimension in either direction
        if width <= max_dimension and height <= max_dimension:
            logger.info(f"Image size OK for memory: {width}x{height}")
            return image
        
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_dimension
            new_height = int((height * max_dimension) / width)
        else:
            new_height = max_dimension
            new_width = int((width * max_dimension) / height)
        
        # Resize using high-quality resampling
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        new_pixels = new_width * new_height
        reduction_percent = ((original_pixels - new_pixels) / original_pixels) * 100
        
        logger.info(f"Image resized for memory optimization: {width}x{height} -> {new_width}x{new_height} ({reduction_percent:.1f}% reduction)")
        
        return resized_image
