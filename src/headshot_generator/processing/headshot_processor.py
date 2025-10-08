"""Enhanced headshot processing with OpenCV face detection and PIL image processing."""

from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import cv2
import numpy as np
from PIL import Image, ImageOps

from ..utils.exceptions import ImageProcessingError, FaceDetectionError, ValidationError
from ..utils.logger import get_logger
from ..constants import DEFAULT_FACE_DETECTION_PARAMS
from ..models.image_data import ImageData

logger = get_logger(__name__)


class HeadshotProcessor:
    """Enhanced headshot processor with robust error handling and logging."""
    
    def __init__(self, cascade_path: Optional[str] = None):
        """
        Initialize the headshot processor.
        
        Args:
            cascade_path: Path to Haar cascade file. If None, uses OpenCV default.
        """
        self.cascade_path = cascade_path or (cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self._face_cascade = None
        self._validate_cascade()
        
        logger.info(f"HeadshotProcessor initialized with cascade: {self.cascade_path}")
    
    def _validate_cascade(self) -> None:
        """Validate that the cascade file exists and is accessible."""
        cascade_file = Path(self.cascade_path)
        if not cascade_file.exists():
            raise ImageProcessingError(
                f"Haar cascade file not found: {self.cascade_path}",
                "Face detection system is not properly configured. Please contact support."
            )
        
        try:
            self._face_cascade = cv2.CascadeClassifier(self.cascade_path)
            if self._face_cascade.empty():
                raise ImageProcessingError(
                    f"Failed to load cascade classifier: {self.cascade_path}",
                    "Face detection system failed to initialize. Please contact support."
                )
        except Exception as e:
            raise ImageProcessingError(
                f"Error loading cascade classifier: {e}",
                "Face detection system encountered an error. Please contact support."
            )
        
        logger.debug("Cascade classifier validated and loaded")
    
    def process_image(
        self,
        image_data: ImageData,
        processing_params: Dict[str, Any]
    ) -> Image.Image:
        """
        Process an image to create a headshot.
        
        Args:
            image_data: ImageData object containing the image to process
            processing_params: Dictionary with processing parameters
            
        Returns:
            Processed PIL Image
            
        Raises:
            ValidationError: If input validation fails
            ImageProcessingError: If processing fails
            FaceDetectionError: If face detection fails
        """
        logger.info("Starting headshot processing")
        
        # Validate inputs
        image_data.validate_for_processing()
        self._validate_processing_params(processing_params)
        
        try:
            # Extract parameters
            target_size = (processing_params["target_width"], processing_params["target_height"])
            padding_ratios = {
                "top": processing_params["padding_top_ratio"],
                "bottom": processing_params["padding_bottom_ratio"],
                "side": processing_params["padding_side_ratio"],
            }
            border_color = processing_params["border_color"]
            zoom_out_factor = processing_params["zoom_out_factor"]
            shift_x = processing_params["shift_x"]
            shift_y = processing_params["shift_y"]
            grayscale = processing_params.get("grayscale", False)
            
            logger.debug(f"Processing parameters: {processing_params}")
            
            # Convert PIL image to OpenCV format
            input_image = image_data.original_image
            img_array = np.array(input_image)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            logger.debug(f"Image converted to OpenCV format: {img_cv.shape}")
            
            # Detect faces
            faces = self._detect_faces(gray)
            
            # Process based on face detection results
            if len(faces) == 0:
                logger.warning("No faces detected, using center crop")
                cropped = self._center_crop(input_image, target_size, zoom_out_factor, shift_x, shift_y)
            else:
                logger.info(f"Detected {len(faces)} face(s), using face-based crop")
                face = faces[0]  # Use the first (largest) detected face
                cropped = self._face_crop(
                    input_image, img_cv, face, padding_ratios, 
                    target_size, zoom_out_factor, shift_x, shift_y
                )
            
            # Resize and add borders
            final_image = self._finalize_image(cropped, target_size, border_color)
            
            # Apply grayscale conversion if requested
            if grayscale:
                final_image = self._convert_to_grayscale(final_image)
                logger.debug("Applied grayscale conversion")
            
            # Update image data with results
            image_data.set_processed_image(final_image, processing_params)
            
            logger.info(f"Successfully processed headshot: {final_image.size}")
            return final_image
            
        except (ValidationError, ImageProcessingError, FaceDetectionError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during image processing: {e}")
            raise ImageProcessingError(
                f"Unexpected processing error: {e}",
                "An unexpected error occurred while processing the image. Please try again."
            )
    
    def _validate_processing_params(self, params: Dict[str, Any]) -> None:
        """Validate processing parameters."""
        required_keys = [
            "target_width", "target_height", "padding_top_ratio", "padding_bottom_ratio",
            "padding_side_ratio", "border_color", "zoom_out_factor", "shift_x", "shift_y"
        ]
        
        for key in required_keys:
            if key not in params:
                raise ValidationError(
                    f"Missing required parameter: {key}",
                    "Processing parameters are incomplete. Please check the configuration."
                )
        
        # Validate parameter ranges
        if params["target_width"] <= 0 or params["target_height"] <= 0:
            raise ValidationError(
                f"Invalid target dimensions: {params['target_width']}x{params['target_height']}",
                "Target width and height must be positive values."
            )
        
        if not (0.5 <= params["zoom_out_factor"] <= 3.0):
            raise ValidationError(
                f"Invalid zoom factor: {params['zoom_out_factor']}",
                "Zoom out factor must be between 0.5 and 3.0."
            )
    
    def _detect_faces(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Detect faces in the grayscale image.
        
        Args:
            gray_image: Grayscale image as numpy array
            
        Returns:
            Array of detected faces
            
        Raises:
            FaceDetectionError: If face detection fails
        """
        try:
            faces = self._face_cascade.detectMultiScale(
                gray_image,
                scaleFactor=DEFAULT_FACE_DETECTION_PARAMS["scaleFactor"],
                minNeighbors=DEFAULT_FACE_DETECTION_PARAMS["minNeighbors"],
                minSize=DEFAULT_FACE_DETECTION_PARAMS["minSize"]
            )
            
            logger.debug(f"Face detection completed: {len(faces)} faces found")
            return faces
            
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            raise FaceDetectionError(
                f"Face detection error: {e}",
                "Face detection failed. Please ensure the image contains a clear face and try again."
            )
    
    def _convert_to_grayscale(self, image: Image.Image) -> Image.Image:
        """Convert a PIL image to grayscale while preserving 3-channel mode for consistent saving."""
        # Convert to grayscale (single channel)
        gray_img = ImageOps.grayscale(image)
        # Convert back to RGB so downstream saving options remain consistent
        return gray_img.convert("RGB")
    
    
    def _center_crop(
        self,
        image: Image.Image,
        target_size: Tuple[int, int],
        zoom_out_factor: float,
        shift_x: int,
        shift_y: int
    ) -> Image.Image:
        """Create center crop when no face is detected."""
        width, height = image.size
        target_ratio = target_size[0] / target_size[1]
        
        # Calculate base crop dimensions
        base_crop_width = min(width, int(height * target_ratio))
        base_crop_height = min(height, int(width / target_ratio))
        
        # Apply zoom out factor
        crop_width = int(base_crop_width * zoom_out_factor)
        crop_height = int(base_crop_height * zoom_out_factor)
        
        # Calculate crop position with shifts
        crop_left = (width - crop_width) // 2 + shift_x
        crop_top = (height - crop_height) // 2 + shift_y
        crop_right = crop_left + crop_width
        crop_bottom = crop_top + crop_height
        
        # Ensure crop stays within image bounds
        crop_left, crop_top, crop_right, crop_bottom = self._constrain_crop_bounds(
            crop_left, crop_top, crop_right, crop_bottom, width, height
        )
        
        return image.crop((crop_left, crop_top, crop_right, crop_bottom))
    
    def _face_crop(
        self,
        image: Image.Image,
        img_cv: np.ndarray,
        face: Tuple[int, int, int, int],
        padding_ratios: Dict[str, float],
        target_size: Tuple[int, int],
        zoom_out_factor: float,
        shift_x: int,
        shift_y: int
    ) -> Image.Image:
        """Create face-based crop."""
        x, y, w, h = face
        
        # Calculate padding
        padding_top = int(h * padding_ratios["top"])
        padding_bottom = int(h * padding_ratios["bottom"])
        padding_side = int(w * padding_ratios["side"])
        
        # Calculate crop dimensions with zoom
        crop_width = int((w + 2 * padding_side) * zoom_out_factor)
        crop_height = int((h + padding_top + padding_bottom) * zoom_out_factor)
        
        # Calculate crop position centered on face with shifts
        crop_left = x + w//2 - crop_width//2 + shift_x
        crop_right = crop_left + crop_width
        crop_top = y + h//2 - crop_height//2 + shift_y
        crop_bottom = crop_top + crop_height
        
        # Constrain to image bounds
        img_height, img_width = img_cv.shape[:2]
        crop_left, crop_top, crop_right, crop_bottom = self._constrain_crop_bounds(
            crop_left, crop_top, crop_right, crop_bottom, img_width, img_height
        )
        
        # Adjust crop to match target aspect ratio
        crop_width = crop_right - crop_left
        crop_height = crop_bottom - crop_top
        target_ratio = target_size[0] / target_size[1]
        
        if crop_width / crop_height > target_ratio:
            # Crop is too wide, adjust height
            new_height = int(crop_width / target_ratio)
            crop_top = max(0, crop_top - (new_height - crop_height) // 2)
            crop_bottom = min(img_height, crop_top + new_height)
        else:
            # Crop is too tall, adjust width
            new_width = int(crop_height * target_ratio)
            crop_left = max(0, crop_left - (new_width - crop_width) // 2)
            crop_right = min(img_width, crop_left + new_width)
        
        return image.crop((crop_left, crop_top, crop_right, crop_bottom))
    
    def _constrain_crop_bounds(
        self,
        left: int, top: int, right: int, bottom: int,
        img_width: int, img_height: int
    ) -> Tuple[int, int, int, int]:
        """Constrain crop bounds to image dimensions."""
        # Adjust for bounds
        if left < 0:
            right -= left
            left = 0
        if top < 0:
            bottom -= top
            top = 0
        if right > img_width:
            left -= (right - img_width)
            right = img_width
        if bottom > img_height:
            top -= (bottom - img_height)
            bottom = img_height
        
        # Final bounds check
        left = max(0, left)
        top = max(0, top)
        right = min(img_width, right)
        bottom = min(img_height, bottom)
        
        return left, top, right, bottom
    
    def _finalize_image(
        self,
        cropped: Image.Image,
        target_size: Tuple[int, int],
        border_color: str
    ) -> Image.Image:
        """Finalize the image by resizing and adding borders."""
        # Resize maintaining aspect ratio
        cropped.thumbnail(target_size, Image.LANCZOS)
        
        # Add borders to match exact target size
        final_img = ImageOps.expand(
            cropped,
            border=(
                (target_size[0] - cropped.width) // 2,
                (target_size[1] - cropped.height) // 2
            ),
            fill=border_color
        )
        
        # Ensure exact target size
        final_img = final_img.resize(target_size, Image.LANCZOS)
        
        return final_img