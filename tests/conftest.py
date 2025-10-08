"""Pytest configuration and fixtures for headshot generator tests."""

import pytest
from PIL import Image
import io
import tempfile
from pathlib import Path

from headshot_generator.utils.config import ConfigManager
from headshot_generator.models.image_data import ImageData
from headshot_generator.models.session_state import SessionState, ProcessingParameters


@pytest.fixture
def sample_image():
    """Create a sample PIL image for testing."""
    # Create a simple 500x500 RGB image
    image = Image.new('RGB', (500, 500), color='white')
    return image


@pytest.fixture
def sample_uploaded_file(sample_image):
    """Create a mock uploaded file object for testing."""
    class MockUploadedFile:
        def __init__(self, image):
            self.name = "test_image.jpg"
            self.type = "image/jpeg"
            self.size = 50000
            
            # Convert image to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            buffer.seek(0)
            self._buffer = buffer
        
        def read(self, size=-1):
            return self._buffer.read(size)
        
        def seek(self, pos):
            return self._buffer.seek(pos)
        
        def getvalue(self):
            return self._buffer.getvalue()
    
    return MockUploadedFile(sample_image)


@pytest.fixture
def test_config():
    """Create test configuration dictionary."""
    return {
        "default": {
            "target_width": 400,
            "target_height": 500,
            "padding_top": 0.2,
            "padding_bottom": 0.5,
            "padding_side": 0.1,
            "border_color": "#000000",
            "shift_x": 0,
            "shift_y": 0,
            "zoom_out_factor": 1.1
        },
        "linkedin": {
            "target_width": 400,
            "target_height": 400,
            "padding_top": 0.3,
            "padding_bottom": 0.3,
            "padding_side": 0.2,
            "border_color": "#F3F2EF",
            "shift_x": 0,
            "shift_y": 0,
            "zoom_out_factor": 1.2
        },
        "slider": {
            "target_width_min": 200,
            "target_width_max": 1000,
            "target_height_min": 200,
            "target_height_max": 1000,
            "padding_min": 0.0,
            "padding_top_max": 0.5,
            "padding_bottom_max": 1.0,
            "padding_side_max": 0.5,
            "shift_min": -100,
            "shift_max": 100,
            "zoom_out_min": 0.9,
            "zoom_out_max": 2.0
        },
        "download_formats": {
            "jpeg": {
                "format": "JPEG",
                "extension": ".jpg",
                "mime": "image/jpeg",
                "quality": 95,
                "optimize": True
            }
        }
    }


@pytest.fixture
def temp_config_file(test_config, tmp_path):
    """Create a temporary config file for testing."""
    import toml
    config_file = tmp_path / "config.toml"
    with open(config_file, 'w') as f:
        toml.dump(test_config, f)
    return str(config_file)


@pytest.fixture
def image_data_with_image(sample_image):
    """Create ImageData instance with a sample image."""
    image_data = ImageData()
    image_data.original_image = sample_image
    image_data.original_dimensions = sample_image.size
    image_data.filename = "test.jpg"
    image_data.format = "JPEG"
    return image_data


@pytest.fixture
def processing_parameters():
    """Create default processing parameters."""
    return ProcessingParameters()


@pytest.fixture 
def session_state():
    """Create a default session state."""
    return SessionState()