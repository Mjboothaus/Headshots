"""Configuration management for the headshot generator application."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import toml

from .exceptions import ConfigurationError
from .logger import get_logger
from ..constants import CONFIG_FILE

logger = get_logger(__name__)


class ConfigManager:
    """Manages application configuration from TOML files."""
    
    def __init__(self, config_path: str = CONFIG_FILE):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from the TOML file."""
        try:
            if not self.config_path.exists():
                raise ConfigurationError(
                    f"Configuration file not found: {self.config_path}",
                    f"Configuration file '{self.config_path}' is missing. "
                    "Please ensure it exists in the application directory."
                )
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = toml.load(f)
            
            logger.info(f"Configuration loaded from {self.config_path}")
            self._validate_config()
            
        except toml.TomlDecodeError as e:
            raise ConfigurationError(
                f"Failed to parse TOML configuration: {e}",
                "Configuration file is invalid. Please check the syntax and try again."
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration: {e}",
                "Unable to load configuration. Please check the file permissions and try again."
            )
    
    def _validate_config(self) -> None:
        """Validate the loaded configuration."""
        required_sections = ['default', 'slider']
        
        for section in required_sections:
            if section not in self._config:
                raise ConfigurationError(
                    f"Missing required configuration section: {section}",
                    f"Configuration is incomplete. Missing '{section}' section."
                )
        
        # Validate default section has required keys
        required_default_keys = [
            'target_width', 'target_height', 'padding_top', 'padding_bottom',
            'padding_side', 'border_color', 'shift_x', 'shift_y', 'zoom_out_factor'
        ]
        
        default_config = self._config.get('default', {})
        for key in required_default_keys:
            if key not in default_config:
                raise ConfigurationError(
                    f"Missing required key '{key}' in default configuration",
                    "Configuration is incomplete. Please check the default settings."
                )
        
        logger.info("Configuration validation passed")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def get_presets(self) -> List[str]:
        """
        Get available preset names (excluding system sections).
        
        Returns:
            List of preset names
        """
        system_sections = {'slider', 'download_formats', 'ui'}
        return [
            key.title() 
            for key in self._config.keys() 
            if key not in system_sections
        ]
    
    def get_preset_config(self, preset_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific preset.
        
        Args:
            preset_name: Name of the preset
            
        Returns:
            Preset configuration dictionary
            
        Raises:
            ConfigurationError: If preset not found
        """
        preset_key = preset_name.lower()
        if preset_key not in self._config:
            raise ConfigurationError(
                f"Preset '{preset_name}' not found in configuration",
                f"Preset '{preset_name}' is not available. Please choose from the available presets."
            )
        
        return self._config[preset_key]
    
    def get_download_formats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get download format configurations.
        
        Returns:
            Dictionary of download formats and their settings
        """
        return self._config.get('download_formats', {})
    
    def get_ui_config(self, key: str = None) -> Any:
        """
        Get UI configuration values.
        
        Args:
            key: Specific UI config key (e.g., 'app_title', 'labels.profile_selector')
                If None, returns the entire UI config
        
        Returns:
            UI configuration value or dictionary
        """
        ui_config = self._config.get('ui', {})
        
        if key is None:
            return ui_config
        
        # Handle nested keys like 'labels.profile_selector'
        keys = key.split('.')
        value = ui_config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def reload(self) -> None:
        """Reload configuration from file."""
        logger.info("Reloading configuration")
        self.load_config()
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self._config.copy()