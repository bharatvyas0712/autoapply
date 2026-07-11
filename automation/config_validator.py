"""
Environment configuration validation for AutoJobApply automation service.
Ensures all required environment variables are set and valid.
"""

import os
import sys
from typing import Dict, List, Optional
from logger_config import logger


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigValidator:
    """Validates environment configuration for the automation service."""
    
    REQUIRED_VARS = {
        'PORT': {'type': int, 'default': 5001, 'description': 'Flask server port'},
        'FORM_AGENT_SERVICE_URL': {'type': str, 'default': 'http://localhost:5006', 'description': 'Form agent service URL'},
    }
    
    OPTIONAL_VARS = {
        'AUTOJOBAPPLY_LOGIN_WAIT_SECONDS': {'type': int, 'default': 600, 'description': 'Login wait timeout in seconds'},
        'AUTOJOBAPPLY_LOGIN_POLL_INTERVAL_SECONDS': {'type': int, 'default': 3, 'description': 'Login poll interval in seconds'},
        'AUTOJOBAPPLY_FIELD_REVIEW_TIMEOUT_SECONDS': {'type': int, 'default': 900, 'description': 'Field review timeout in seconds'},
        'AUTOJOBAPPLY_REVIEW_POLL_INTERVAL_SECONDS': {'type': int, 'default': 5, 'description': 'Review poll interval in seconds'},
        'AUTOJOBAPPLY_PROFILE_DIR': {'type': str, 'default': None, 'description': 'Browser profile directory path'},
        'AUTOJOBAPPLY_PROFILE_DIRECTORY': {'type': str, 'default': None, 'description': 'Chrome profile directory name'},
    }
    
    @classmethod
    def validate(cls) -> Dict[str, any]:
        """
        Validate all environment variables.
        
        Returns:
            Dictionary containing validated configuration values
            
        Raises:
            ConfigValidationError: If validation fails
        """
        config = {}
        errors = []
        
        # Validate required variables
        for var_name, var_config in cls.REQUIRED_VARS.items():
            value = os.environ.get(var_name)
            if value is None:
                if 'default' in var_config:
                    value = var_config['default']
                    logger.warning(f"Using default value for {var_name}: {value}")
                else:
                    errors.append(f"Required environment variable {var_name} is not set")
                    continue
            
            try:
                if var_config['type'] == int:
                    config[var_name] = int(value)
                elif var_config['type'] == str:
                    config[var_name] = str(value)
                else:
                    config[var_name] = value
                logger.debug(f"Validated {var_name}: {config[var_name]}")
            except (ValueError, TypeError) as e:
                errors.append(f"Invalid value for {var_name}: {value} (expected {var_config['type']})")
        
        # Validate optional variables
        for var_name, var_config in cls.OPTIONAL_VARS.items():
            value = os.environ.get(var_name)
            if value is None:
                if var_config['default'] is not None:
                    config[var_name] = var_config['default']
                    logger.debug(f"Using default value for {var_name}: {config[var_name]}")
                continue
            
            try:
                if var_config['type'] == int:
                    config[var_name] = int(value)
                elif var_config['type'] == str:
                    config[var_name] = str(value)
                else:
                    config[var_name] = value
                logger.debug(f"Validated {var_name}: {config[var_name]}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid value for optional variable {var_name}: {value}. Using default.")
                if var_config['default'] is not None:
                    config[var_name] = var_config['default']
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ConfigValidationError(error_msg)
        
        logger.info("Configuration validation successful")
        return config
    
    @classmethod
    def print_config_summary(cls, config: Dict[str, any]):
        """Print a summary of the current configuration."""
        logger.info("=" * 60)
        logger.info("AutoJobApply Automation Service Configuration")
        logger.info("=" * 60)
        
        for var_name, value in config.items():
            var_info = cls.REQUIRED_VARS.get(var_name) or cls.OPTIONAL_VARS.get(var_name)
            if var_info:
                logger.info(f"{var_name}: {value} ({var_info.get('description', 'N/A')})")
        
        logger.info("=" * 60)


def validate_and_get_config() -> Dict[str, any]:
    """
    Validate configuration and return config dictionary.
    This is the main entry point for configuration validation.
    """
    try:
        config = ConfigValidator.validate()
        ConfigValidator.print_config_summary(config)
        return config
    except ConfigValidationError as e:
        logger.error(str(e))
        sys.exit(1)
