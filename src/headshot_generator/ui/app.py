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
        # Try to get UI config, fallback to defaults if not available
        try:
            page_title = self.config_manager.get_ui_config('page_title') or "Headshot Creator"
            page_icon = self.config_manager.get_ui_config('page_icon') or "📸"
        except:
            page_title = "Headshot Creator"
            page_icon = "📸"
            
        st.set_page_config(
            page_title=page_title,
            page_icon=page_icon,
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
            
            # Main page header - use config values
            app_title = self.config_manager.get_ui_config('app_title') or "Headshot Creator"
            app_description = self.config_manager.get_ui_config('app_description') or "Upload an image and adjust settings to generate a headshot with real-time preview."
            
            st.markdown(f"# {app_title}")
            st.write(app_description)
            
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
            file_upload_label = self.config_manager.get_ui_config('labels.file_upload') or "Choose an image to get started"
            file_upload_help = self.config_manager.get_ui_config('labels.file_upload_help') or "Upload a PNG or JPG image to process into a headshot."
            
            uploaded_file = st.file_uploader(
                file_upload_label,
                type=["png", "jpg", "jpeg"],
                help=file_upload_help
            )
            
            # Handle file upload
            if uploaded_file is not None:
                # Show temporary file size warning for large files
                if hasattr(uploaded_file, 'size') and uploaded_file.size:
                    file_size_mb = uploaded_file.size / (1024 * 1024)
                    max_size_mb = self.config_manager.get_ui_config('max_file_size_warning_mb') or 5.0
                    
                    if file_size_mb > max_size_mb:
                        warning_template = self.config_manager.get_ui_config('labels.file_size_warning') or "⚠️ Large file detected: {size:.1f}MB. Image will be automatically optimised for better performance."
                        warning_placeholder = st.empty()
                        warning_placeholder.warning(warning_template.format(size=file_size_mb))
                        
                        # Clear warning after 3 seconds
                        import time
                        time.sleep(3)
                        warning_placeholder.empty()
                
                self._handle_file_upload(uploaded_file)
        
        with col2:
            profile_label = self.config_manager.get_ui_config('labels.profile_selector') or "Profile:"
            st.markdown(f"**{profile_label}**")
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
        """Render the profile selection using dropdown with alphabetized options."""
        try:
            # Get available presets and add Custom
            available_presets = self.config_manager.get_presets()
            preset_options = available_presets + ["Custom"]
            
            # Sort alphabetically (Custom will be first due to capital C)
            preset_options.sort()
            
            # Get display icons from config
            profile_icons = self.config_manager.get_ui_config('profile_icons') or {}
            
            # Create format function for display
            def format_preset(preset):
                return profile_icons.get(preset, f"📋 {preset}")
            
            # Get current selection (default to first option if not found)
            current_selection = st.session_state.app_state.selected_preset
            if current_selection not in preset_options:
                current_selection = preset_options[0] if preset_options else "Default"
            
            # Find the index for the current selection
            try:
                current_index = preset_options.index(current_selection)
            except ValueError:
                current_index = 0
            
            profile_help = self.config_manager.get_ui_config('labels.profile_help') or "Choose a preset profile or select 'Custom' to manually adjust settings"
            
            selected_preset = st.selectbox(
                "Profile",
                options=preset_options,
                index=current_index,
                format_func=format_preset,
                help=profile_help,
                label_visibility="collapsed",
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
        """Render the image display section with memory optimization."""
        col1, col2 = st.columns(2)
        
        # Get UI labels from config
        original_label = self.config_manager.get_ui_config('labels.original_image') or "Original Image"
        processed_label = self.config_manager.get_ui_config('labels.processed_image') or "Processed Headshot"
        original_caption = self.config_manager.get_ui_config('labels.original_caption') or "Before (Original)"
        processed_caption = self.config_manager.get_ui_config('labels.processed_caption') or "After (Processed)"
        upload_prompt = self.config_manager.get_ui_config('labels.upload_prompt') or "📷 Upload an image using the sidebar to get started"
        processed_prompt = self.config_manager.get_ui_config('labels.processed_prompt') or "✨ Your processed headshot will appear here"
        
        with col1:
            st.subheader(original_label)
            if st.session_state.image_data.original_image is not None:
                # Use optimized display size for better performance
                display_image = self._optimize_image_for_display(
                    st.session_state.image_data.original_image
                )
                st.image(
                    display_image,
                    caption=original_caption,
                    use_container_width=True  # Updated from deprecated use_column_width
                )
            else:
                st.info(upload_prompt)
        
        with col2:
            st.subheader(processed_label)
            if st.session_state.image_data.processed_image is not None:
                # Use optimized display size for better performance
                display_image = self._optimize_image_for_display(
                    st.session_state.image_data.processed_image
                )
                st.image(
                    display_image,
                    caption=processed_caption,
                    use_container_width=True  # Updated from deprecated use_column_width
                )
            else:
                st.info(processed_prompt)
    
    def _render_download_section(self) -> None:
        """Render the download section with segmented control and editable filename."""
        if (st.session_state.image_data.processed_image is not None and 
            st.session_state.image_data.original_image is not None):
            
            st.markdown("---")
            section_title = self.config_manager.get_ui_config('labels.download_section') or "💾 Download Headshot"
            st.subheader(section_title)
            
            try:
                # Get download formats from config
                formats = self.config_manager.get_download_formats()
                
                if formats:
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        format_label = self.config_manager.get_ui_config('labels.download_format') or "Format:"
                        st.markdown(f"**{format_label}**")
                        
                        format_options = list(formats.keys())
                        # Use segmented control for format selection
                        selected_format = st.segmented_control(
                            "Format Selection",
                            options=format_options,
                            default=format_options[0],
                            label_visibility="collapsed",
                            key="format_selector"
                        )
                    
                    with col2:
                        filename_label = self.config_manager.get_ui_config('labels.download_filename') or "Filename:"
                        st.markdown(f"**{filename_label}**")
                        
                        # Generate default filename
                        default_filename = self._generate_filename(selected_format, formats[selected_format])
                        
                        # Editable filename input
                        custom_filename = st.text_input(
                            "Custom filename",
                            value=default_filename,
                            label_visibility="collapsed",
                            key="custom_filename"
                        )
                        
                        # Download button with custom filename
                        self._render_download_button_with_filename(
                            selected_format, 
                            formats[selected_format], 
                            custom_filename
                        )
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
    
    def _optimize_image_for_display(self, image: Image.Image, max_display_size: int = 800) -> Image.Image:
        """
        Optimize image for display in Streamlit to reduce memory usage.
        
        Args:
            image: PIL Image to optimize for display
            max_display_size: Maximum dimension for display (default: 800px)
            
        Returns:
            Display-optimized PIL Image
        """
        width, height = image.size
        
        # Only resize if image is larger than display size
        if width <= max_display_size and height <= max_display_size:
            return image
        
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_display_size
            new_height = int((height * max_display_size) / width)
        else:
            new_height = max_display_size
            new_width = int((width * max_display_size) / height)
        
        # Create display copy (don't modify original)
        display_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        logger.debug(f"Display image optimized: {width}x{height} -> {new_width}x{new_height}")
        
        return display_image
    
    def _generate_filename(self, format_key: str, format_info: Dict[str, Any]) -> str:
        """
        Generate default filename based on template from config.
        
        Args:
            format_key: Format key (e.g., 'jpeg')
            format_info: Format information dictionary
        
        Returns:
            Generated filename
        """
        template = self.config_manager.get_ui_config('default_filename_template') or "headshot_{preset}{grayscale_suffix}{extension}"
        
        preset_name = st.session_state.app_state.selected_preset.lower()
        grayscale_suffix = "_bw" if st.session_state.app_state.processing_params.grayscale else ""
        extension = format_info['extension']
        
        return template.format(
            preset=preset_name,
            grayscale_suffix=grayscale_suffix,
            extension=extension
        )
    
    def _render_download_button_with_filename(
        self, 
        format_key: str, 
        format_info: Dict[str, Any], 
        filename: str
    ) -> None:
        """
        Render download button with custom filename.
        
        Args:
            format_key: Format key
            format_info: Format information dictionary
            filename: Custom filename
        """
        try:
            # Generate image buffer
            buffer = io.BytesIO()
            save_kwargs = {"format": format_info["format"]}
            
            if format_info.get("quality"):
                save_kwargs["quality"] = format_info["quality"]
            if format_info.get("optimize"):
                save_kwargs["optimize"] = format_info["optimize"]
            
            st.session_state.image_data.processed_image.save(buffer, **save_kwargs)
            
            # Get button label template from config
            button_template = self.config_manager.get_ui_config('labels.download_button') or "💾 Download as {format}"
            button_label = button_template.format(format=format_info['format'].upper())
            
            st.download_button(
                label=button_label,
                data=buffer.getvalue(),
                file_name=filename,
                mime=format_info["mime"],
                help=f"Download the processed headshot as {format_info['format']} format (filename: {filename})",
                use_container_width=True
            )
            
        except Exception as e:
            logger.error(f"Download button error: {e}")
            st.error("Error generating download file.")
