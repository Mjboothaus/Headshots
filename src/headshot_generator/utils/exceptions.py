"""Custom exception classes for the headshot generator application."""

from typing import Optional


class HeadshotGeneratorError(Exception):
    """Base exception class for all headshot generator errors."""
    
    def __init__(self, message: str, user_message: Optional[str] = None):
        """
        Initialize the exception.
        
        Args:
            message: Technical error message for logging
            user_message: User-friendly message to display in the UI
        """
        super().__init__(message)
        self.user_message = user_message or message


class ValidationError(HeadshotGeneratorError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, user_message: Optional[str] = None):
        if user_message is None:
            user_message = (
                "Invalid input provided. Please check your settings and try again."
            )
        super().__init__(message, user_message)


class ImageProcessingError(HeadshotGeneratorError):
    """Raised when image processing fails."""
    
    def __init__(self, message: str, user_message: Optional[str] = None):
        if user_message is None:
            user_message = (
                "Failed to process the image. Please try with a different image "
                "or adjust the settings."
            )
        super().__init__(message, user_message)


class ConfigurationError(HeadshotGeneratorError):
    """Raised when configuration loading or validation fails."""
    
    def __init__(self, message: str, user_message: Optional[str] = None):
        if user_message is None:
            user_message = (
                "Configuration error. Please check the config.toml file "
                "or contact support."
            )
        super().__init__(message, user_message)


class FileError(HeadshotGeneratorError):
    """Raised when file operations fail."""
    
    def __init__(self, message: str, user_message: Optional[str] = None):
        if user_message is None:
            user_message = (
                "File operation failed. Please ensure the file is accessible "
                "and try again."
            )
        super().__init__(message, user_message)


class FaceDetectionError(ImageProcessingError):
    """Raised when face detection fails or finds unexpected results."""
    
    def __init__(self, message: str, user_message: Optional[str] = None):
        if user_message is None:
            user_message = (
                "Face detection failed. Please ensure the image contains a clear, "
                "front-facing portrait and try again."
            )
        super().__init__(message, user_message)