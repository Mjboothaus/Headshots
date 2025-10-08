"""
Headshot Generator Package

A Streamlit application for processing portrait images into professional headshots
using OpenCV face detection and PIL image processing.
"""

__version__ = "2.0.0"
__author__ = "Your Name"

from .ui.app import HeadshotApp

__all__ = ["HeadshotApp"]