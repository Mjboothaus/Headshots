"""Tests for HeadshotProcessor."""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from PIL import Image
import pathlib

from headshot_generator.processing.headshot_processor import HeadshotProcessor
from headshot_generator.utils.exceptions import ImageProcessingError, ValidationError


class TestHeadshotProcessor:
    """Test HeadshotProcessor functionality."""
    
    @pytest.fixture
    def mock_processor(self):
        """Fixture to create a properly mocked HeadshotProcessor."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('cv2.data.haarcascades', '/mock/path/'), \
             patch('cv2.CascadeClassifier') as mock_cascade:
            
            mock_cascade_instance = MagicMock()
            mock_cascade_instance.empty.return_value = False
            mock_cascade.return_value = mock_cascade_instance
            
            processor = HeadshotProcessor()
            yield processor

    @patch('cv2.CascadeClassifier')
    @patch('cv2.data.haarcascades', '/mock/path/')
    @patch('pathlib.Path.exists', return_value=True)
    def test_processor_initialization(self, mock_path_exists, mock_cascade):
        """Test processor initialization."""
        mock_cascade_instance = MagicMock()
        mock_cascade_instance.empty.return_value = False
        mock_cascade.return_value = mock_cascade_instance
        
        processor = HeadshotProcessor()
        
        assert processor is not None
        assert processor._face_cascade is not None

    def test_validate_processing_params_valid(self, mock_processor):
        """Test validation of valid processing parameters."""
        processor = mock_processor
        valid_params = {
            "target_width": 400,
            "target_height": 500,
            "padding_top_ratio": 0.2,
            "padding_bottom_ratio": 0.5,
            "padding_side_ratio": 0.1,
            "border_color": "#000000",
            "zoom_out_factor": 1.1,
            "shift_x": 0,
            "shift_y": 0
        }
        
        # Should not raise any exception
        processor._validate_processing_params(valid_params)

    def test_validate_processing_params_missing_key(self, mock_processor):
        """Test validation error for missing parameter."""
        processor = mock_processor
        invalid_params = {
            "target_width": 400,
            # Missing other required parameters
        }
        
        with pytest.raises(ValidationError) as excinfo:
            processor._validate_processing_params(invalid_params)
        
        assert "incomplete" in excinfo.value.user_message

    def test_validate_processing_params_invalid_dimensions(self, mock_processor):
        """Test validation error for invalid dimensions."""
        processor = mock_processor
        invalid_params = {
            "target_width": 0,
            "target_height": 500,
            "padding_top_ratio": 0.2,
            "padding_bottom_ratio": 0.5,
            "padding_side_ratio": 0.1,
            "border_color": "#000000",
            "zoom_out_factor": 1.1,
            "shift_x": 0,
            "shift_y": 0
        }
        
        with pytest.raises(ValidationError) as excinfo:
            processor._validate_processing_params(invalid_params)
        
        assert "positive values" in excinfo.value.user_message

    def test_validate_processing_params_invalid_zoom(self, mock_processor):
        """Test validation error for invalid zoom factor."""
        processor = mock_processor
        invalid_params = {
            "target_width": 400,
            "target_height": 500,
            "padding_top_ratio": 0.2,
            "padding_bottom_ratio": 0.5,
            "padding_side_ratio": 0.1,
            "border_color": "#000000",
            "zoom_out_factor": 5.0,  # Invalid zoom factor
            "shift_x": 0,
            "shift_y": 0
        }
        
        with pytest.raises(ValidationError) as excinfo:
            processor._validate_processing_params(invalid_params)
        
        assert "between 0.5 and 3.0" in excinfo.value.user_message

    @patch('cv2.CascadeClassifier')
    @patch('cv2.data.haarcascades', '/mock/path/')
    @patch('pathlib.Path.exists', return_value=True)
    def test_detect_faces_success(self, mock_path_exists, mock_cascade):
        """Test successful face detection."""
        # Mock the cascade classifier
        mock_cascade_instance = MagicMock()
        mock_cascade_instance.empty.return_value = False
        mock_cascade_instance.detectMultiScale.return_value = np.array([[100, 100, 200, 200]])
        mock_cascade.return_value = mock_cascade_instance
        
        processor = HeadshotProcessor()
        gray_image = np.zeros((500, 500), dtype=np.uint8)
        
        faces = processor._detect_faces(gray_image)
        
        assert len(faces) == 1
        assert faces[0][0] == 100  # x coordinate

    @patch('cv2.CascadeClassifier')
    @patch('cv2.data.haarcascades', '/mock/path/')
    @patch('pathlib.Path.exists', return_value=True)
    def test_detect_faces_no_faces(self, mock_path_exists, mock_cascade):
        """Test face detection with no faces found."""
        # Mock the cascade classifier
        mock_cascade_instance = MagicMock()
        mock_cascade_instance.empty.return_value = False
        mock_cascade_instance.detectMultiScale.return_value = np.array([])  # No faces
        mock_cascade.return_value = mock_cascade_instance
        
        processor = HeadshotProcessor()
        gray_image = np.zeros((500, 500), dtype=np.uint8)
        
        faces = processor._detect_faces(gray_image)
        
        assert len(faces) == 0

    def test_constrain_crop_bounds(self, mock_processor):
        """Test crop bounds constraining."""
        processor = mock_processor
        
        # Test normal case
        left, top, right, bottom = processor._constrain_crop_bounds(
            50, 50, 450, 450, 500, 500
        )
        assert left == 50
        assert top == 50
        assert right == 450
        assert bottom == 450
        
        # Test bounds correction
        left, top, right, bottom = processor._constrain_crop_bounds(
            -10, -10, 510, 510, 500, 500
        )
        assert left == 0
        assert top == 0
        assert right == 500
        assert bottom == 500

    def test_center_crop(self, mock_processor, sample_image):
        """Test center crop functionality."""
        processor = mock_processor
        
        cropped = processor._center_crop(
            sample_image, 
            target_size=(400, 500), 
            zoom_out_factor=1.0,
            shift_x=0,
            shift_y=0
        )
        
        assert isinstance(cropped, Image.Image)
        assert cropped.size[0] <= sample_image.size[0]
        assert cropped.size[1] <= sample_image.size[1]

    def test_finalize_image(self, mock_processor, sample_image):
        """Test image finalization."""
        processor = mock_processor
        
        # Create a smaller image to test resizing
        small_image = sample_image.resize((300, 300))
        
        final_image = processor._finalize_image(
            small_image,
            target_size=(400, 500),
            border_color="#000000"
        )
        
        assert isinstance(final_image, Image.Image)
        assert final_image.size == (400, 500)