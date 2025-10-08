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
        
        logger.info("Image data cleared")