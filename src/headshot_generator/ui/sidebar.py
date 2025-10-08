"""Sidebar UI component for the headshot generator application."""

from typing import Dict, Any, Tuple

import streamlit as st

from ..utils.config import ConfigManager
from ..utils.logger import get_logger
from ..models.session_state import SessionState

logger = get_logger(__name__)


class Sidebar:
    """Manages the sidebar interface for manual adjustments."""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the sidebar.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        logger.debug("Sidebar initialized")
    
    def render(self, session_state: SessionState) -> Tuple[Dict[str, Any], str]:
        """
        Render the sidebar controls and return updated parameters.
        
        Args:
            session_state: Current session state
            
        Returns:
            Tuple of (updated_params, border_color)
        """
        st.sidebar.title("Manual Adjustments")
        
        # Get current parameters
        params = session_state.processing_params
        
        # Get slider configuration
        slider_config = self.config_manager.get("slider", {})
        
        # Dimensions section
        st.sidebar.subheader("Dimensions")
        with st.sidebar:
            col1, col2 = st.columns(2)
            with col1:
                target_width = st.slider(
                    "Width (px)",
                    slider_config.get("target_width_min", 200),
                    slider_config.get("target_width_max", 1000),
                    params.target_width,
                    10,
                    help="Set the final width of the headshot in pixels.",
                    key="target_width"
                )
            with col2:
                target_height = st.slider(
                    "Height (px)",
                    slider_config.get("target_height_min", 200),
                    slider_config.get("target_height_max", 1000),
                    params.target_height,
                    10,
                    help="Set the final height of the headshot in pixels.",
                    key="target_height"
                )
        
        # Padding section
        st.sidebar.subheader("Padding")
        with st.sidebar:
            col1, col2 = st.columns(2)
            with col1:
                padding_top = st.slider(
                    "Top Ratio",
                    slider_config.get("padding_min", 0.0),
                    slider_config.get("padding_top_max", 0.5),
                    params.padding_top,
                    0.01,
                    help="Add space above the face (as a fraction of face height) for headroom.",
                    key="padding_top"
                )
                padding_bottom = st.slider(
                    "Bottom Ratio",
                    slider_config.get("padding_min", 0.0),
                    slider_config.get("padding_bottom_max", 1.0),
                    params.padding_bottom,
                    0.01,
                    help="Add space below the face (as a fraction of face height) for shoulders.",
                    key="padding_bottom"
                )
            with col2:
                padding_side = st.slider(
                    "Side Ratio",
                    slider_config.get("padding_min", 0.0),
                    slider_config.get("padding_side_max", 0.5),
                    params.padding_side,
                    0.01,
                    help="Add space on the left and right of the face (as a fraction of face width).",
                    key="padding_side"
                )
        
        # Position & Zoom section
        st.sidebar.subheader("Position & Zoom")
        with st.sidebar:
            col1, col2 = st.columns(2)
            with col1:
                shift_x = st.slider(
                    "Shift X (px)",
                    slider_config.get("shift_min", -100),
                    slider_config.get("shift_max", 100),
                    params.shift_x,
                    5,
                    help="Move the crop box left (negative) or right (positive) in pixels.",
                    key="shift_x"
                )
                shift_y = st.slider(
                    "Shift Y (px)",
                    slider_config.get("shift_min", -100),
                    slider_config.get("shift_max", 100),
                    params.shift_y,
                    5,
                    help="Move the crop box up (negative) or down (positive) in pixels.",
                    key="shift_y"
                )
            with col2:
                zoom_out_factor = st.slider(
                    "Zoom Factor",
                    slider_config.get("zoom_out_min", 0.9),
                    slider_config.get("zoom_out_max", 2.0),
                    params.zoom_out_factor,
                    0.05,
                    help="Scale the crop box size (1.0 = no zoom-out, 1.5 = 50% larger crop).",
                    key="zoom_out_factor"
                )
        
        # Appearance section
        st.sidebar.subheader("Appearance")
        border_color = st.sidebar.color_picker(
            "Border Colour",
            params.border_color,
            help="Used when image doesn't match target aspect ratio",
            key="border_color"
        )
        
        grayscale = st.sidebar.checkbox(
            "Black & White",
            value=params.grayscale,
            help="Convert the output image to grayscale (black and white)",
            key="grayscale"
        )
        
        # Collect all parameters
        updated_params = {
            "target_width": target_width,
            "target_height": target_height,
            "padding_top": padding_top,
            "padding_bottom": padding_bottom,
            "padding_side": padding_side,
            "shift_x": shift_x,
            "shift_y": shift_y,
            "zoom_out_factor": zoom_out_factor,
            "border_color": border_color,
            "grayscale": grayscale
        }
        
        # Log parameter changes
        changed_params = {
            key: value for key, value in updated_params.items()
            if getattr(params, key, None) != value
        }
        
        if changed_params:
            logger.debug(f"Sidebar parameter changes: {changed_params}")
        
        return updated_params, border_color
    
    def has_parameter_changes(
        self, 
        current_params: Dict[str, Any], 
        session_state: SessionState
    ) -> bool:
        """
        Check if any parameters have changed from the session state.
        
        Args:
            current_params: Current parameter values from UI
            session_state: Current session state
            
        Returns:
            True if parameters have changed
        """
        stored_params = session_state.processing_params
        
        return (
            current_params["target_width"] != stored_params.target_width or
            current_params["target_height"] != stored_params.target_height or
            current_params["padding_top"] != stored_params.padding_top or
            current_params["padding_bottom"] != stored_params.padding_bottom or
            current_params["padding_side"] != stored_params.padding_side or
            current_params["shift_x"] != stored_params.shift_x or
            current_params["shift_y"] != stored_params.shift_y or
            current_params["zoom_out_factor"] != stored_params.zoom_out_factor or
            current_params["border_color"] != stored_params.border_color or
            current_params["grayscale"] != stored_params.grayscale
        )
