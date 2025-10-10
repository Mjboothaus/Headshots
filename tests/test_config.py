"""Tests for configuration management."""

import pytest
from pathlib import Path

from headshot_curator.utils.config import ConfigManager
from headshot_curator.utils.exceptions import ConfigurationError


class TestConfigManager:
    """Test configuration manager functionality."""

    def test_load_valid_config(self, temp_config_file):
        """Test loading a valid configuration file."""
        config_manager = ConfigManager(temp_config_file)
        
        assert config_manager.get("default") is not None
        assert config_manager.get("default")["target_width"] == 400
        assert config_manager.get("slider") is not None

    def test_load_missing_config(self, tmp_path):
        """Test error handling for missing configuration file."""
        missing_config = tmp_path / "missing.toml"
        
        with pytest.raises(ConfigurationError) as excinfo:
            ConfigManager(str(missing_config))
        
        assert "not found" in str(excinfo.value)

    def test_get_presets(self, temp_config_file):
        """Test getting available presets."""
        config_manager = ConfigManager(temp_config_file)
        presets = config_manager.get_presets()
        
        assert "Default" in presets
        assert "Linkedin" in presets
        assert len(presets) >= 2

    def test_get_preset_config(self, temp_config_file):
        """Test getting specific preset configuration."""
        config_manager = ConfigManager(temp_config_file)
        
        # Test default preset
        default_config = config_manager.get_preset_config("Default")
        assert default_config["target_width"] == 400
        
        # Test linkedin preset
        linkedin_config = config_manager.get_preset_config("LinkedIn")
        assert linkedin_config["target_width"] == 400
        assert linkedin_config["target_height"] == 400

    def test_get_invalid_preset(self, temp_config_file):
        """Test error handling for invalid preset."""
        config_manager = ConfigManager(temp_config_file)
        
        with pytest.raises(ConfigurationError) as excinfo:
            config_manager.get_preset_config("InvalidPreset")
        
        assert "not found" in str(excinfo.value)

    def test_get_download_formats(self, temp_config_file):
        """Test getting download format configurations."""
        config_manager = ConfigManager(temp_config_file)
        formats = config_manager.get_download_formats()
        
        assert "jpeg" in formats
        assert formats["jpeg"]["format"] == "JPEG"
        assert formats["jpeg"]["extension"] == ".jpg"

    def test_validation_missing_sections(self, tmp_path):
        """Test configuration validation with missing sections."""
        import toml
        invalid_config = {"default": {}}  # Missing required keys
        
        config_file = tmp_path / "invalid.toml"
        with open(config_file, 'w') as f:
            toml.dump(invalid_config, f)
        
        with pytest.raises(ConfigurationError):
            ConfigManager(str(config_file))