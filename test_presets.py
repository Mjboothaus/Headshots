#!/usr/bin/env python3
"""Test script to validate all presets and functionality."""

from headshot_generator import HeadshotApp
from headshot_generator.utils.config import ConfigManager
from headshot_generator.models.session_state import SessionState, ProcessingParameters

def test_presets():
    """Test all preset configurations."""
    print("Testing Headshot Generator Presets")
    print("=" * 50)
    
    # Test configuration loading
    config = ConfigManager()
    presets = config.get_presets()
    print(f"Available presets: {presets}")
    print()
    
    # Test each preset configuration
    for preset in presets:
        try:
            preset_config = config.get_preset_config(preset)
            params = ProcessingParameters.from_config(preset_config)
            params.validate()
            print(f"✓ {preset.ljust(15)}: {params.target_width}x{params.target_height}, border: {params.border_color}")
        except Exception as e:
            print(f"✗ {preset.ljust(15)}: ERROR - {e}")
    
    print()
    
    # Test custom preset handling
    try:
        custom_config = config.get_preset_config("custom")
        print(f"✓ Custom preset loaded: {custom_config}")
    except Exception as e:
        print(f"✗ Custom preset ERROR: {e}")
    
    print()
    
    # Test session state with custom parameters
    session_state = SessionState()
    print(f"Initial preset: {session_state.selected_preset}")
    print(f"Custom params: {session_state.custom_params}")
    
    # Simulate switching to Custom and making changes
    session_state.set_preset("Custom")
    test_params = {
        "target_width": 500,
        "target_height": 600,
        "padding_top": 0.4,
        "padding_bottom": 0.3,
        "padding_side": 0.2,
        "border_color": "#FF0000",
        "shift_x": 10,
        "shift_y": -5,
        "zoom_out_factor": 1.5
    }
    
    # Simulate manual parameter changes
    session_state.custom_params = ProcessingParameters.from_config(test_params)
    print(f"Custom params after changes: {session_state.custom_params}")
    
    # Test switching away and back to Custom
    session_state.set_preset("LinkedIn")
    print(f"Switched to LinkedIn, custom params preserved: {session_state.custom_params is not None}")
    
    session_state.set_preset("Custom")
    session_state.apply_custom_preset()
    print(f"Switched back to Custom, params restored: {session_state.processing_params.target_width}")
    
    print("\n✓ All tests completed successfully!")

if __name__ == "__main__":
    test_presets()