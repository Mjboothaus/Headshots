"""Tests for ImageData model."""

import pytest
from PIL import Image
import io

from headshot_generator.models.image_data import ImageData
from headshot_generator.utils.exceptions import ValidationError, ImageProcessingError


class TestImageData:
    """Test ImageData functionality."""

    def test_create_empty_image_data(self):
        """Test creating empty ImageData instance."""
        image_data = ImageData()
        
        assert image_data.original_image is None
        assert image_data.processed_image is None
        assert image_data.filename is None
        assert image_data.get_aspect_ratio() is None

    def test_from_uploaded_file_valid(self, sample_uploaded_file):
        """Test creating ImageData from valid uploaded file."""
        image_data = ImageData.from_uploaded_file(sample_uploaded_file)
        
        assert image_data.original_image is not None
        assert image_data.filename == "test_image.jpg"
        assert image_data.format == "JPG"
        assert image_data.original_dimensions == (500, 500)
        assert image_data.upload_time is not None

    def test_from_uploaded_file_none(self):
        """Test error handling for None uploaded file."""
        with pytest.raises(ValidationError) as excinfo:
            ImageData.from_uploaded_file(None)
        
        assert "select an image file" in excinfo.value.user_message

    def test_from_uploaded_file_invalid_type(self):
        """Test error handling for invalid file type."""
        class MockInvalidFile:
            name = "test.txt"
            type = "text/plain"
        
        with pytest.raises(ValidationError) as excinfo:
            ImageData.from_uploaded_file(MockInvalidFile())
        
        assert "supported image format" in excinfo.value.user_message

    def test_from_uploaded_file_too_small(self):
        """Test error handling for image too small."""
        # Create tiny image
        tiny_image = Image.new('RGB', (50, 50), color='white')
        
        class MockTinyFile:
            name = "tiny.jpg"
            type = "image/jpeg"
            
            def __init__(self):
                buffer = io.BytesIO()
                tiny_image.save(buffer, format='JPEG')
                buffer.seek(0)
                self._buffer = buffer
            
            def read(self, size=-1):
                return self._buffer.read(size)
            
            def seek(self, pos):
                return self._buffer.seek(pos)
        
        with pytest.raises(ValidationError) as excinfo:
            ImageData.from_uploaded_file(MockTinyFile())
        
        assert "at least 100x100 pixels" in excinfo.value.user_message

    def test_set_processed_image(self, sample_image, image_data_with_image):
        """Test setting processed image."""
        processing_params = {"target_width": 400, "target_height": 500}
        
        image_data_with_image.set_processed_image(sample_image, processing_params)
        
        assert image_data_with_image.processed_image is not None
        assert image_data_with_image.processed_dimensions == (500, 500)
        assert image_data_with_image.processing_params == processing_params
        assert image_data_with_image.processing_time is not None

    def test_validate_for_processing_valid(self, image_data_with_image):
        """Test validation for valid image data."""
        # Should not raise any exception
        image_data_with_image.validate_for_processing()

    def test_validate_for_processing_no_image(self):
        """Test validation error for missing image."""
        image_data = ImageData()
        
        with pytest.raises(ValidationError) as excinfo:
            image_data.validate_for_processing()
        
        assert "upload an image" in excinfo.value.user_message

    def test_get_aspect_ratio(self, image_data_with_image):
        """Test aspect ratio calculation."""
        aspect_ratio = image_data_with_image.get_aspect_ratio()
        assert aspect_ratio == 1.0  # 500x500 image

    def test_get_processing_summary(self, image_data_with_image):
        """Test getting processing summary."""
        summary = image_data_with_image.get_processing_summary()
        
        assert "filename" in summary
        assert "original_size" in summary
        assert "format" in summary
        assert "aspect_ratio" in summary
        assert summary["filename"] == "test.jpg"
        assert summary["original_size"] == (500, 500)

    def test_clear(self, image_data_with_image):
        """Test clearing image data."""
        image_data_with_image.clear()
        
        assert image_data_with_image.original_image is None
        assert image_data_with_image.processed_image is None
        assert image_data_with_image.filename is None
        assert image_data_with_image.original_dimensions is None