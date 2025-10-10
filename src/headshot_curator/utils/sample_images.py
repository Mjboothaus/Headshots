"""Sample images utility for the Headshot Curator application."""

import os
from pathlib import Path
from typing import List, Dict, Optional
import streamlit as st
from PIL import Image

from .logger import get_logger
from .config import ConfigManager

logger = get_logger(__name__)


class SampleImageManager:
    """Manages sample images for testing the application."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize the sample image manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.samples_dir = Path(config_manager.get_ui_config('sample_images.directory') or 'images/samples')
        self.enabled = config_manager.get_ui_config('sample_images.enabled') or True
        logger.info(f"SampleImageManager initialized with directory: {self.samples_dir.absolute()}") 
    
    def get_sample_images(self) -> List[Dict[str, str]]:
        """Get list of available sample images.
        
        Returns:
            List of dictionaries containing image info (name, path, display_name)
        """
        if not self.enabled:
            return []
        
        sample_images = []
        
        if not self.samples_dir.exists():
            logger.warning(f"Sample images directory does not exist: {self.samples_dir}")
            # Try to create the directory in case it's missing
            try:
                self.samples_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created sample images directory: {self.samples_dir}")
            except Exception as e:
                logger.error(f"Could not create sample images directory: {e}")
            return []
        
        # Supported image extensions
        supported_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        
        try:
            # Find all image files in the samples directory
            for file_path in self.samples_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    # Create a user-friendly display name
                    display_name = self._create_display_name(file_path.stem)
                    
                    sample_images.append({
                        'name': file_path.stem,
                        'path': str(file_path),
                        'display_name': display_name,
                        'filename': file_path.name
                    })
            
            # Sort by display name for consistent ordering
            sample_images.sort(key=lambda x: x['display_name'])
            
            logger.info(f"Found {len(sample_images)} sample images")
            return sample_images
            
        except Exception as e:
            logger.error(f"Error scanning sample images directory: {e}")
            return []
    
    def _create_display_name(self, filename_stem: str) -> str:
        """Create a user-friendly display name from filename.
        
        Args:
            filename_stem: File name without extension
            
        Returns:
            User-friendly display name
        """
        # Convert underscores and hyphens to spaces
        display_name = filename_stem.replace('_', ' ').replace('-', ' ')
        
        # Capitalize each word
        display_name = ' '.join(word.capitalize() for word in display_name.split())
        
        return display_name
    
    def load_sample_image(self, image_path: str) -> Optional[Image.Image]:
        """Load a sample image from path.
        
        Args:
            image_path: Path to the sample image
            
        Returns:
            PIL Image object or None if loading fails
        """
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                logger.error(f"Sample image not found: {image_path}")
                return None
            
            image = Image.open(image_path)
            # Convert to RGB if needed
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
                
            logger.info(f"Successfully loaded sample image: {image_path.name}")
            return image
            
        except Exception as e:
            logger.error(f"Error loading sample image {image_path}: {e}")
            return None
    
    def render_sample_selector(self) -> Optional[str]:
        """Render the sample image selector UI.
        
        Returns:
            Selected sample image path or None
        """
        if not self.enabled:
            return None
        
        sample_images = self.get_sample_images()
        
        if not sample_images:
            no_images_msg = self.config_manager.get_ui_config('sample_images.no_images_message') or 'No sample images found.'
            st.info(no_images_msg)
            return None
        
        # Title and help
        title = self.config_manager.get_ui_config('sample_images.title') or '🤖 Try Sample Images'
        help_text = self.config_manager.get_ui_config('sample_images.help') or 'Test the app with sample images'
        
        st.markdown(f"**{title}**")
        
        # Create options for selectbox with placeholder
        placeholder_text = "Choose a sample image..."
        options = [placeholder_text] + [img['display_name'] for img in sample_images]
        
        selected_display_name = st.selectbox(
            "Choose a sample image:",
            options=options,
            index=0,
            help=help_text,
            key="sample_image_selector"
        )
        
        if selected_display_name and selected_display_name != placeholder_text:
            # Find the corresponding image info
            selected_image = next(
                (img for img in sample_images if img['display_name'] == selected_display_name),
                None
            )
            
            if selected_image:
                # Show disclaimer
                disclaimer = self.config_manager.get_ui_config('sample_images.disclaimer') or '⚠️ Note: Sample images are AI-generated'
                st.caption(disclaimer)
                
                return selected_image['path']
        
        return None