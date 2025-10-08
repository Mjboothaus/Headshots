"""Tests for SessionState model."""

import pytest

from headshot_generator.models.session_state import SessionState, ProcessingParameters
from headshot_generator.utils.exceptions import ValidationError


class TestProcessingParameters:
    """Test ProcessingParameters functionality."""

    def test_default_parameters(self):
        """Test default parameter values."""
        params = ProcessingParameters()
        
        assert params.target_width == 400
        assert params.target_height == 500
        assert params.padding_top == 0.2
        assert params.border_color == "#000000"
        assert params.zoom_out_factor == 1.1

    def test_to_dict(self):
        """Test converting parameters to dictionary."""
        params = ProcessingParameters()
        param_dict = params.to_dict()
        
        assert "target_width" in param_dict
        assert "padding_top_ratio" in param_dict
        assert param_dict["target_width"] == 400
        assert param_dict["padding_top_ratio"] == 0.2

    def test_from_config(self):
        """Test creating parameters from configuration."""
        config = {
            "target_width": 300,
            "target_height": 400,
            "padding_top": 0.3,
            "border_color": "#FFFFFF"
        }
        
        params = ProcessingParameters.from_config(config)
        
        assert params.target_width == 300
        assert params.target_height == 400
        assert params.padding_top == 0.3
        assert params.border_color == "#FFFFFF"

    def test_validate_valid_params(self):
        """Test validation of valid parameters."""
        params = ProcessingParameters()
        # Should not raise any exception
        params.validate()

    def test_validate_invalid_dimensions(self):
        """Test validation error for invalid dimensions."""
        params = ProcessingParameters(target_width=0)
        
        with pytest.raises(ValidationError) as excinfo:
            params.validate()
        
        assert "positive values" in excinfo.value.user_message

    def test_validate_invalid_zoom_factor(self):
        """Test validation error for invalid zoom factor."""
        params = ProcessingParameters(zoom_out_factor=5.0)
        
        with pytest.raises(ValidationError) as excinfo:
            params.validate()
        
        assert "between 0.9 and 3.0" in excinfo.value.user_message

    def test_validate_invalid_padding(self):
        """Test validation error for invalid padding."""
        params = ProcessingParameters(padding_top=3.0)
        
        with pytest.raises(ValidationError) as excinfo:
            params.validate()
        
        assert "between 0.0 and 2.0" in excinfo.value.user_message


class TestSessionState:
    """Test SessionState functionality."""

    def test_default_session_state(self):
        """Test default session state values."""
        state = SessionState()
        
        assert state.selected_preset == "Default"
        assert state.show_instructions is False
        assert state.last_error is None
        assert isinstance(state.processing_params, ProcessingParameters)

    def test_update_processing_params(self):
        """Test updating processing parameters."""
        state = SessionState()
        
        state.update_processing_params(target_width=300, padding_top=0.3)
        
        assert state.processing_params.target_width == 300
        assert state.processing_params.padding_top == 0.3

    def test_apply_preset(self):
        """Test applying preset configuration."""
        state = SessionState()
        preset_config = {
            "target_width": 350,
            "target_height": 450,
            "padding_top": 0.25,
            "border_color": "#CCCCCC"
        }
        
        state.apply_preset(preset_config)
        
        assert state.processing_params.target_width == 350
        assert state.processing_params.target_height == 450
        assert state.processing_params.padding_top == 0.25
        assert state.processing_params.border_color == "#CCCCCC"

    def test_apply_invalid_preset(self):
        """Test error handling for invalid preset."""
        state = SessionState()
        invalid_config = {"target_width": -100}  # Invalid value
        
        with pytest.raises(ValidationError):
            state.apply_preset(invalid_config)

    def test_set_preset(self):
        """Test setting preset name."""
        state = SessionState()
        
        state.set_preset("LinkedIn")
        
        assert state.selected_preset == "LinkedIn"

    def test_toggle_instructions(self):
        """Test toggling instructions display."""
        state = SessionState()
        
        assert state.show_instructions is False
        state.toggle_instructions()
        assert state.show_instructions is True
        state.toggle_instructions()
        assert state.show_instructions is False

    def test_error_handling(self):
        """Test error message handling."""
        state = SessionState()
        
        assert state.last_error is None
        
        state.set_error("Test error message")
        assert state.last_error == "Test error message"
        
        state.clear_error()
        assert state.last_error is None

    def test_get_processing_dict(self):
        """Test getting processing parameters as dictionary."""
        state = SessionState()
        processing_dict = state.get_processing_dict()
        
        assert isinstance(processing_dict, dict)
        assert "target_width" in processing_dict
        assert "padding_top_ratio" in processing_dict

    def test_validate_state(self):
        """Test state validation."""
        state = SessionState()
        # Should not raise any exception
        state.validate_state()

    def test_reset_to_defaults(self):
        """Test resetting to default values."""
        state = SessionState()
        
        # Modify some values
        state.set_preset("LinkedIn")
        state.set_error("Some error")
        state.update_processing_params(target_width=300)
        
        # Reset
        state.reset_to_defaults()
        
        assert state.selected_preset == "Default"
        assert state.last_error is None
        assert state.processing_params.target_width == 400  # Default value

    def test_get_state_summary(self):
        """Test getting state summary."""
        state = SessionState()
        summary = state.get_state_summary()
        
        assert "selected_preset" in summary
        assert "show_instructions" in summary
        assert "has_error" in summary
        assert "processing_params" in summary
        assert summary["selected_preset"] == "Default"
        assert summary["has_error"] is False