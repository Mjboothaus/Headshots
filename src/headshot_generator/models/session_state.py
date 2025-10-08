"""SessionState model for managing UI and processing state."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from ..utils.logger import get_logger
from ..utils.exceptions import ValidationError

logger = get_logger(__name__)


@dataclass
class ProcessingParameters:
    """Processing parameters for headshot generation."""
    
    target_width: int = 400
    target_height: int = 500
    padding_top: float = 0.2
    padding_bottom: float = 0.5
    padding_side: float = 0.1
    border_color: str = "#000000"
    shift_x: int = 0
    shift_y: int = 0
    zoom_out_factor: float = 1.1
    grayscale: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for processing."""
        return {
            "target_width": self.target_width,
            "target_height": self.target_height,
            "padding_top_ratio": self.padding_top,
            "padding_bottom_ratio": self.padding_bottom,
            "padding_side_ratio": self.padding_side,
            "border_color": self.border_color,
            "shift_x": self.shift_x,
            "shift_y": self.shift_y,
            "zoom_out_factor": self.zoom_out_factor,
            "grayscale": self.grayscale
        }
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'ProcessingParameters':
        """Create from configuration dictionary."""
        return cls(
            target_width=config.get("target_width", 400),
            target_height=config.get("target_height", 500),
            padding_top=config.get("padding_top", 0.2),
            padding_bottom=config.get("padding_bottom", 0.5),
            padding_side=config.get("padding_side", 0.1),
            border_color=config.get("border_color", "#000000"),
            shift_x=config.get("shift_x", 0),
            shift_y=config.get("shift_y", 0),
            zoom_out_factor=config.get("zoom_out_factor", 1.1),
            grayscale=config.get("grayscale", False)
        )
    
    def validate(self) -> None:
        """Validate processing parameters."""
        if self.target_width <= 0 or self.target_height <= 0:
            raise ValidationError(
                f"Invalid target dimensions: {self.target_width}x{self.target_height}",
                "Target width and height must be positive values."
            )
        
        if not (0.9 <= self.zoom_out_factor <= 3.0):
            raise ValidationError(
                f"Invalid zoom factor: {self.zoom_out_factor}",
                "Zoom out factor must be between 0.9 and 3.0."
            )
        
        if not all(0.0 <= p <= 2.0 for p in [self.padding_top, self.padding_bottom, self.padding_side]):
            raise ValidationError(
                "Invalid padding values",
                "Padding ratios must be between 0.0 and 2.0."
            )


@dataclass
class SessionState:
    """Manages application session state."""
    
    processing_params: ProcessingParameters = field(default_factory=ProcessingParameters)
    selected_preset: str = "Default"
    custom_params: Optional[ProcessingParameters] = None  # Store custom parameters separately
    show_instructions: bool = False
    last_error: Optional[str] = None
    
    def __post_init__(self):
        """Initialize session state."""
        logger.info("Session state initialized")
    
    def update_processing_params(self, **kwargs) -> None:
        """
        Update processing parameters.
        
        Args:
            **kwargs: Parameter updates
        """
        for key, value in kwargs.items():
            if hasattr(self.processing_params, key):
                setattr(self.processing_params, key, value)
                logger.debug(f"Updated processing param {key}: {value}")
            else:
                logger.warning(f"Unknown processing parameter: {key}")
    
    def apply_preset(self, preset_config: Dict[str, Any]) -> None:
        """
        Apply a preset configuration to processing parameters.
        
        Args:
            preset_config: Configuration dictionary for the preset
        """
        try:
            self.processing_params = ProcessingParameters.from_config(preset_config)
            self.processing_params.validate()
            logger.info(f"Applied preset configuration: {preset_config}")
        except Exception as e:
            logger.error(f"Failed to apply preset: {e}")
            raise ValidationError(
                f"Invalid preset configuration: {e}",
                "The selected preset has invalid settings. Please choose a different preset."
            )
    
    def set_preset(self, preset_name: str) -> None:
        """
        Set the selected preset name.
        
        Args:
            preset_name: Name of the selected preset
        """
        # If switching FROM Custom, save current params as custom params
        if self.selected_preset == "Custom" and preset_name != "Custom":
            self.custom_params = ProcessingParameters(
                target_width=self.processing_params.target_width,
                target_height=self.processing_params.target_height,
                padding_top=self.processing_params.padding_top,
                padding_bottom=self.processing_params.padding_bottom,
                padding_side=self.processing_params.padding_side,
                border_color=self.processing_params.border_color,
                shift_x=self.processing_params.shift_x,
                shift_y=self.processing_params.shift_y,
                zoom_out_factor=self.processing_params.zoom_out_factor,
                grayscale=self.processing_params.grayscale
            )
            logger.info("Saved current parameters as custom preset")
        
        self.selected_preset = preset_name
        logger.info(f"Selected preset: {preset_name}")
    
    def apply_custom_preset(self) -> None:
        """
        Apply saved custom parameters if available, otherwise use config custom preset.
        """
        if self.custom_params is not None:
            self.processing_params = ProcessingParameters(
                target_width=self.custom_params.target_width,
                target_height=self.custom_params.target_height,
                padding_top=self.custom_params.padding_top,
                padding_bottom=self.custom_params.padding_bottom,
                padding_side=self.custom_params.padding_side,
                border_color=self.custom_params.border_color,
                shift_x=self.custom_params.shift_x,
                shift_y=self.custom_params.shift_y,
                zoom_out_factor=self.custom_params.zoom_out_factor,
                grayscale=self.custom_params.grayscale
            )
            logger.info("Applied saved custom parameters")
        else:
            logger.info("No saved custom parameters, will use config custom preset")
    
    def toggle_instructions(self) -> None:
        """Toggle the instructions display state."""
        self.show_instructions = not self.show_instructions
        logger.debug(f"Instructions visibility: {self.show_instructions}")
    
    def set_error(self, error_message: str) -> None:
        """
        Set the last error message.
        
        Args:
            error_message: Error message to store
        """
        self.last_error = error_message
        logger.error(f"Session error set: {error_message}")
    
    def clear_error(self) -> None:
        """Clear the last error message."""
        if self.last_error:
            logger.debug("Cleared session error")
        self.last_error = None
    
    def get_processing_dict(self) -> Dict[str, Any]:
        """
        Get processing parameters as a dictionary.
        
        Returns:
            Dictionary of processing parameters
        """
        return self.processing_params.to_dict()
    
    def validate_state(self) -> None:
        """
        Validate the current session state.
        
        Raises:
            ValidationError: If state validation fails
        """
        try:
            self.processing_params.validate()
            logger.debug("Session state validation passed")
        except Exception as e:
            logger.error(f"Session state validation failed: {e}")
            raise
    
    def reset_to_defaults(self) -> None:
        """Reset processing parameters to defaults."""
        self.processing_params = ProcessingParameters()
        self.selected_preset = "Default"
        self.clear_error()
        logger.info("Session state reset to defaults")
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current session state.
        
        Returns:
            Dictionary with state summary
        """
        return {
            "selected_preset": self.selected_preset,
            "show_instructions": self.show_instructions,
            "has_error": self.last_error is not None,
            "processing_params": self.get_processing_dict()
        }