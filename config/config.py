"""
Configuration management for AthenaOSINT.

This module handles loading and validating environment variables
and application settings.
"""

import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from pathlib import Path
from loguru import logger


class Config:
    """Configuration manager for AthenaOSINT."""
    
    def __init__(self):
        """Initialize configuration by loading .env file."""
        # Load environment variables from .env file
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(dotenv_path=env_path)
        
        # Load all configuration
        self._config = self._load_all_config()
        
        # Validate critical settings
        self._validate_config()
    
    def _load_all_config(self) -> Dict[str, any]:
        """Load all configuration from environment variables.
        
        Returns:
            Dictionary containing all configuration values
        """
        config = {
            # API Keys - Support comma-separated values for rotation
            'HIBP_API_KEYS': self._parse_list(os.getenv('HIBP_API_KEY', '')),
            'DEHASHED_API_KEYS': self._parse_list(os.getenv('DEHASHED_API_KEY', '')),
            'DEHASHED_USERNAME': os.getenv('DEHASHED_USERNAME', ''),
            'INTELX_API_KEYS': self._parse_list(os.getenv('INTELX_API_KEY', '')),
            'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
            'SHODAN_API_KEYS': self._parse_list(os.getenv('SHODAN_API_KEY', '')),
            'VIRUSTOTAL_API_KEYS': self._parse_list(os.getenv('VIRUSTOTAL_API_KEY', '')),
            'HUNTER_API_KEYS': self._parse_list(os.getenv('HUNTER_API_KEY', '')),
            'GROQ_API_KEYS': self._parse_list(os.getenv('GROQ_API_KEY', '')),
            'GITHUB_API_KEYS': self._parse_list(os.getenv('GITHUB_API_KEY', '')),
            
            # Flask settings
            'FLASK_ENV': os.getenv('FLASK_ENV', 'development'),
            'FLASK_SECRET_KEY': os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex()),
            'FLASK_HOST': os.getenv('FLASK_HOST', '0.0.0.0'),
            'FLASK_PORT': int(os.getenv('FLASK_PORT', 5000)),
            
            # Application settings
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'MAX_SCAN_DEPTH': int(os.getenv('MAX_SCAN_DEPTH', 3)),
            'RATE_LIMIT': int(os.getenv('RATE_LIMIT', 60)),
            'MODULE_TIMEOUT': int(os.getenv('MODULE_TIMEOUT', 300)),
            
            # AI Settings
            'AI_PROVIDER': os.getenv('AI_PROVIDER', 'groq'),  # groq, ollama, openai
            'OLLAMA_HOST': os.getenv('OLLAMA_HOST', 'http://localhost:11434'),
            'OLLAMA_MODEL': os.getenv('OLLAMA_MODEL', 'llama3:8b'),
            
            # Database
            # Database
            'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///athena.db'),

            # AutoGen
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
            
            # Firecrawl
            'FIRECRAWL_API_KEY': os.getenv('FIRECRAWL_API_KEY', ''),

            # Social Credentials
            'FACEBOOK_EMAIL': os.getenv('FACEBOOK_EMAIL', ''),
            'FACEBOOK_PASSWORD': os.getenv('FACEBOOK_PASSWORD', ''),
            'INSTAGRAM_USER': os.getenv('INSTAGRAM_USER', ''),
            'INSTAGRAM_PASSWORD': os.getenv('INSTAGRAM_PASSWORD', ''),

            # Paths
            'DATA_DIR': Path(__file__).parent.parent / 'data',
            'REPORTS_DIR': Path(__file__).parent.parent / 'reports',
            'LOGS_DIR': Path(__file__).parent.parent / 'logs',
        }
        
        # Ensure directories exist
        for key in ['DATA_DIR', 'REPORTS_DIR', 'LOGS_DIR']:
            config[key].mkdir(parents=True, exist_ok=True)
        
        return config
    
    def _parse_list(self, value: str) -> List[str]:
        """Parse a comma-separated string into a list."""
        if not value:
            return []
        return [item.strip() for item in value.split(',') if item.strip()]

    def _validate_config(self):
        """Validate critical configuration settings."""
        warnings = []
        
        # Check for missing API keys (non-critical)
        if not self._config['HIBP_API_KEYS']:
            warnings.append("HIBP_API_KEY not set - breach checking will be limited")
        
        if not self._config['DEHASHED_API_KEYS']:
            warnings.append("DEHASHED_API_KEY not set - advanced leak checking disabled")
        
        if not self._config['TELEGRAM_BOT_TOKEN']:
            warnings.append("TELEGRAM_BOT_TOKEN not set - bot functionality disabled")
            
        if not self._config['GROQ_API_KEYS'] and self._config['AI_PROVIDER'] == 'groq':
             warnings.append("GROQ_API_KEY not set but provider is 'groq' - AI features may fail")
        
        # Log warnings
        for warning in warnings:
            logger.warning(warning)
    
    def get(self, key: str, default: any = None) -> any:
        """Get a configuration value.
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def get_api_keys(self, service: str) -> List[str]:
        """Get all API keys for a specific service.
        
        Args:
            service: Service name (e.g., 'HIBP', 'SHODAN')
            
        Returns:
            List of API keys
        """
        key_name = f'{service.upper()}_API_KEYS'
        return self._config.get(key_name, [])
    
    def has_api_key(self, service: str) -> bool:
        """Check if at least one API key is configured for a service.
        
        Args:
            service: Service name (e.g., 'HIBP', 'SHODAN')
            
        Returns:
            True if API key is configured, False otherwise
        """
        keys = self.get_api_keys(service)
        return len(keys) > 0


# Global configuration instance
_config_instance: Optional[Config] = None


def load_config() -> Config:
    """Load or retrieve the global configuration instance.
    
    Returns:
        Global Config instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config()
        logger.info("Configuration loaded successfully")
    
    return _config_instance


def get_config() -> Config:
    """Get the global configuration instance.
    
    Returns:
        Global Config instance
    """
    return load_config()
