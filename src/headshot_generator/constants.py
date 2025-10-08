"""Constants used throughout the headshot generator application."""

from typing import List

# File types
SUPPORTED_IMAGE_TYPES: List[str] = ["png", "jpg", "jpeg"]
SUPPORTED_MIME_TYPES: List[str] = ["image/png", "image/jpeg", "image/jpg"]

# Default file paths
CONFIG_FILE: str = "config.toml"
INSTRUCTIONS_FILE: str = "instructions.md"
CASCADE_FILE_DEFAULT: str = "haarcascade_frontalface_default.xml"

# Image processing defaults
DEFAULT_FACE_DETECTION_PARAMS = {
    "scaleFactor": 1.1,
    "minNeighbors": 5,
    "minSize": (30, 30)
}

# UI Constants
PROFILE_COLUMN_RATIO: List[int] = [3, 1]
IMAGE_DISPLAY_COLUMNS: int = 2
DOWNLOAD_FORMAT_COLUMNS: List[int] = [1, 2]

# Logging
LOG_FORMAT: str = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# Session state keys
SESSION_KEYS = {
    "current_image": "current_image",
    "original_image": "original_image", 
    "control_state": "control_state",
    "show_instructions": "show_instructions",
    "last_preset": "last_preset"
}