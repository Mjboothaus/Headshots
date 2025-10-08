"""Main HeadshotApp class for orchestrating the application."""

import io
from pathlib import Path
from typing import Optional, Dict, Any

import streamlit as st
from PIL import Image

from ..utils.config import ConfigManager
from ..utils.logger import setup_logger, get_logger
from ..utils.exceptions import HeadshotGeneratorError
from ..constants import PROFILE_COLUMN_RATIO, INSTRUCTIONS_FILE
from ..models.image_data import ImageData
from ..models.session_state import SessionState, ProcessingParameters
from ..processing.headshot_processor import HeadshotProcessor
from .sidebar import Sidebar

# Initialize logging
setup_logger(log_level="INFO", log_file="logs/headshot_app.log")
logger = get_logger(__name__)


class HeadshotApp:
    """Main application class for the Headshot Generator."""
    
    def __init__(self):
        """Initialize the application."""
        self._setup_page_config()
        
        try:
            # Initialize components
            self.config_manager = ConfigManager()
            self.processor = HeadshotProcessor()
            self.sidebar = Sidebar(self.config_manager)
            
            # Initialize session state
            self._initialize_session_state()
            
            logger.info("HeadshotApp initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize HeadshotApp: {e}")
            st.error(f"Application initialization failed: {e}")
            st.stop()
    
    def _setup_page_config(self) -> None:
        """Set up Streamlit page configuration."""
        st.set_page_config(
            page_title="Headshot Generator",
            page_icon="📸",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        logger.debug("Page configuration set up")
    
    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state."""
        # Initialize ImageData
        if "image_data" not in st.session_state:
            st.session_state.image_data = ImageData()
        
        # Initialize SessionState
        if "app_state" not in st.session_state:
            # Get default configuration
            default_config = self.config_manager.get_preset_config("default")
            initial_params = ProcessingParameters.from_config(default_config)
            
            st.session_state.app_state = SessionState(
                processing_params=initial_params,
                selected_preset="Default"
            )
        
        logger.debug("Session state initialized")
    
    def run(self) -> None:
        """Run the main application."""
        try:
            logger.info("Starting application run")
            
            # Main page header
            st.title("Interactive Headshot Generator")
            st.write("Upload an image and adjust settings to generate a headshot with real-time preview.")
            
            # File upload and profile selection
            self._render_upload_and_profile_section()
            
            # Sidebar controls
            current_params, border_color = self.sidebar.render(st.session_state.app_state)
            
            # Process parameter changes
            self._handle_parameter_changes(current_params)
            
            # Display images
            self._render_image_display()
            
            # Download section
            self._render_download_section()
            
            # Instructions section
            self._render_instructions_section()
            
        except HeadshotGeneratorError as e:
            logger.error(f"Application error: {e}")
            st.error(e.user_message)
        except Exception as e:
            logger.error(f"Unexpected application error: {e}")
            st.error("An unexpected error occurred. Please refresh the page and try again.")
    
    def _render_upload_and_profile_section(self) -> None:
        """Render the file upload and profile selection section."""
        col1, col2 = st.columns(PROFILE_COLUMN_RATIO)
        
        with col1:
            uploaded_file = st.file_uploader(
                "Choose an image to get started",
                type=["png", "jpg", "jpeg"],
                help="Upload a PNG or JPG image to process into a headshot."
            )
            
            # Handle file upload
            if uploaded_file is not None:
                self._handle_file_upload(uploaded_file)
        
        with col2:
            st.markdown("**Profile:**")
            self._render_profile_selector()
    
    def _handle_file_upload(self, uploaded_file) -> None:
        """Handle file upload and validation."""
        try:
            # Create new ImageData from uploaded file
            new_image_data = ImageData.from_uploaded_file(uploaded_file)
            
            # Update session state
            st.session_state.image_data = new_image_data
            
            # Process the image immediately with current settings
            self._process_current_image()
            
            logger.info(f"File uploaded successfully: {uploaded_file.name}")
            
        except HeadshotGeneratorError as e:
            logger.error(f"File upload error: {e}")
            st.error(e.user_message)
            st.session_state.app_state.set_error(str(e))
        except Exception as e:
            logger.error(f"Unexpected upload error: {e}")
            st.error("Failed to process the uploaded file. Please try again.")
    
    def _render_profile_selector(self) -> None:
        """Render the profile selection using segmented control."""
        try:
            # Get available presets
            available_presets = self.config_manager.get_presets()
            
            # Create display names with text-based icons for better UX
            preset_display_map = {
                "Default": "◉ Default",
                "Linkedin": "▣ LinkedIn", 
                "Instagram": "◘ Instagram",
                "Facebook": "◈ Facebook",
                "Twitter": "◐ Twitter",
                "Github": "</> GitHub",
                "About_me": "◎ About.me",
                "Discord": "◇ Discord",
                "Slack": "◆ Slack",
                "Zoom": "◊ Zoom",
                "Professional": "◉ Professional",
                "Passport": "◈ Passport",
                "Custom": "⚙ Custom"
            }
            
            # Filter available options and add Custom
            preset_options = available_presets + ["Custom"]
            display_options = [preset_display_map.get(preset.title(), f"📋 {preset.title()}") for preset in preset_options]
            
            # Get current selection (default to first option if not found)
            current_selection = st.session_state.app_state.selected_preset
            if current_selection not in preset_options:
                current_selection = preset_options[0] if preset_options else "Default"
            
            selected_preset = st.segmented_control(
                "Profile",
                options=preset_options,
                format_func=lambda x: preset_display_map.get(x.title(), f"📋 {x.title()}"),
                default=current_selection,
                help="Choose a preset profile or select 'Custom' to manually adjust settings",
                key="profile_selector"
            )
            
            # Handle preset changes
            if selected_preset and selected_preset != st.session_state.app_state.selected_preset:
                self._handle_preset_change(selected_preset)
                
        except Exception as e:
            logger.error(f"Profile selector error: {e}")
            st.error("Error loading profile options. Please check the configuration.")
    
    def _handle_preset_change(self, selected_preset: str) -> None:
        """Handle preset selection changes."""
        try:
            st.session_state.app_state.set_preset(selected_preset)
            
            if selected_preset == "Custom":
                # For Custom, try to apply saved custom params first
                st.session_state.app_state.apply_custom_preset()
                
                # If no saved custom params, fall back to config custom preset
                if st.session_state.app_state.custom_params is None:
                    preset_config = self.config_manager.get_preset_config(selected_preset)
                    st.session_state.app_state.apply_preset(preset_config)
            else:
                # Apply preset configuration for standard presets
                preset_config = self.config_manager.get_preset_config(selected_preset)
                st.session_state.app_state.apply_preset(preset_config)
            
            # Reprocess image if available
            if st.session_state.image_data.original_image is not None:
                self._process_current_image()
            
            # Force rerun to update sliders
            st.rerun()
            
            logger.info(f"Preset changed to: {selected_preset}")
            
        except HeadshotGeneratorError as e:
            logger.error(f"Preset change error: {e}")
            st.error(e.user_message)
        except Exception as e:
            logger.error(f"Unexpected preset change error: {e}")
            st.error("Failed to apply the selected preset. Please try again.")
    
    def _handle_parameter_changes(self, current_params: Dict[str, Any]) -> None:
        """Handle parameter changes from the sidebar."""
        if self.sidebar.has_parameter_changes(current_params, st.session_state.app_state):
            # Update session state
            st.session_state.app_state.update_processing_params(**current_params)
            
            # If in Custom mode, update the custom_params to persist changes
            if st.session_state.app_state.selected_preset == "Custom":
                # Update custom params with current changes
                st.session_state.app_state.custom_params = ProcessingParameters.from_config(current_params)
                logger.info("Updated custom parameters with manual changes")
            else:
                # Set preset to Custom since manual changes were made to a standard preset
                st.session_state.app_state.set_preset("Custom")
                # Save the modified parameters as custom
                st.session_state.app_state.custom_params = ProcessingParameters.from_config(current_params)
            
            # Reprocess image if available
            if st.session_state.image_data.original_image is not None:
                self._process_current_image()
    
    def _process_current_image(self) -> None:
        """Process the current image with current parameters."""
        try:
            if st.session_state.image_data.original_image is None:
                return
            
            # Get processing parameters
            processing_params = st.session_state.app_state.get_processing_dict()
            
            # Process the image
            processed_image = self.processor.process_image(
                st.session_state.image_data,
                processing_params
            )
            
            logger.info("Image processed successfully")
            
        except HeadshotGeneratorError as e:
            logger.error(f"Image processing error: {e}")
            st.error(e.user_message)
        except Exception as e:
            logger.error(f"Unexpected processing error: {e}")
            st.error("An error occurred while processing the image.")
    
    def _render_image_display(self) -> None:
        """Render the image display section."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Image")
            if st.session_state.image_data.original_image is not None:
                st.image(
                    st.session_state.image_data.original_image,
                    caption="Before (Original)",
                    width="stretch"
                )
            else:
                st.info("📷 Upload an image using the sidebar to get started")
        
        with col2:
            st.subheader("Processed Headshot")
            if st.session_state.image_data.processed_image is not None:
                st.image(
                    st.session_state.image_data.processed_image,
                    caption="After (Processed)",
                    width="stretch"
                )
            else:
                st.info("✨ Your processed headshot will appear here")
    
    def _render_download_section(self) -> None:
        """Render the download section."""
        if (st.session_state.image_data.processed_image is not None and 
            st.session_state.image_data.original_image is not None):
            
            st.markdown("---")
            st.subheader("💾 Download Headshot")
            
            try:
                # Get download formats from config
                formats = self.config_manager.get_download_formats()
                
                if formats:
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown("**Format:**")
                        format_options = list(formats.keys())
                        selected_format = st.radio(
                            "Choose format",
                            format_options,
                            index=0,
                            label_visibility="collapsed",
                            horizontal=True
                        )
                    
                    with col2:
                        self._render_download_button(selected_format, formats[selected_format])
                else:
                    # Fallback to JPEG
                    self._render_fallback_download()
                    
            except Exception as e:
                logger.error(f"Download section error: {e}")
                st.error("Error setting up download options.")
    
    def _render_download_button(self, format_key: str, format_info: Dict[str, Any]) -> None:
        """Render download button for specific format."""
        try:
            # Generate image buffer
            buffer = io.BytesIO()
            save_kwargs = {"format": format_info["format"]}
            
            if format_info.get("quality"):
                save_kwargs["quality"] = format_info["quality"]
            if format_info.get("optimize"):
                save_kwargs["optimize"] = format_info["optimize"]
            
            st.session_state.image_data.processed_image.save(buffer, **save_kwargs)
            
            # Generate dynamic filename based on preset and grayscale setting
            preset_name = st.session_state.app_state.selected_preset.lower()
            grayscale_suffix = "_bw" if st.session_state.app_state.processing_params.grayscale else ""
            filename = f"headshot_{preset_name}{grayscale_suffix}{format_info['extension']}"
            
            st.download_button(
                label=f"💾 Download as {format_info['format'].upper()}",
                data=buffer.getvalue(),
                file_name=filename,
                mime=format_info["mime"],
                help=f"Download the processed headshot as {format_info['format']} format (filename: {filename})",
                width="stretch"
            )
            
        except Exception as e:
            logger.error(f"Download button error: {e}")
            st.error("Error generating download file.")
    
    def _render_fallback_download(self) -> None:
        """Render fallback JPEG download."""
        try:
            buffer = io.BytesIO()
            st.session_state.image_data.processed_image.save(buffer, format="JPEG")
            
            # Generate dynamic filename based on preset and grayscale setting
            preset_name = st.session_state.app_state.selected_preset.lower()
            grayscale_suffix = "_bw" if st.session_state.app_state.processing_params.grayscale else ""
            filename = f"headshot_{preset_name}{grayscale_suffix}.jpg"
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="💾 Download Headshot",
                    data=buffer.getvalue(),
                    file_name=filename,
                    mime="image/jpeg",
                    help=f"Download the processed headshot as a JPEG file (filename: {filename})",
                    width="stretch"
                )
        except Exception as e:
            logger.error(f"Fallback download error: {e}")
            st.error("Error generating download file.")
    
    def _render_instructions_section(self) -> None:
        """Render the instructions toggle section."""
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button(
                "📝 Show Instructions" if not st.session_state.app_state.show_instructions else "🔼 Hide Instructions",
                key="instructions_toggle",
                width="stretch"
            ):
                st.session_state.app_state.toggle_instructions()
                st.rerun()
        
        # Display instructions if toggled on
        if st.session_state.app_state.show_instructions:
            try:
                instructions_path = Path(INSTRUCTIONS_FILE)
                if instructions_path.exists():
                    with open(instructions_path, "r", encoding="utf-8") as f:
                        instructions_content = f.read()
                    st.markdown("")
                    st.markdown(instructions_content)
                else:
                    st.error("Instructions file not found.")
            except Exception as e:
                logger.error(f"Instructions loading error: {e}")
                st.error("Error loading instructions.")