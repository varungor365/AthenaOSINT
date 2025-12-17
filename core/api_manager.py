"""
API Manager for AthenaOSINT.

This module handles API key rotation, rate limiting, and error tracking
for external services.
"""

import time
from typing import Dict, List, Optional
from loguru import logger
from config import get_config


class APIManager:
    """Manages API keys and rotation logic."""
    
    def __init__(self):
        """Initialize the API Manager."""
        self.config = get_config()
        self.key_states: Dict[str, Dict] = {}
        
    def get_key(self, service: str) -> Optional[str]:
        """Get the current active API key for a service.
        
        Args:
            service: Service name (e.g., 'SHODAN', 'GITHUB')
            
        Returns:
            Active API key or None if no keys available
        """
        service = service.upper()
        
        # Initialize state for this service if needed
        if service not in self.key_states:
            keys = self.config.get_api_keys(service)
            if not keys:
                return None
                
            self.key_states[service] = {
                'keys': keys,
                'current_index': 0,
                'exhausted_keys': set(),
                'last_rotation': 0
            }
        
        state = self.key_states[service]
        
        # Check if all keys are exhausted
        if len(state['exhausted_keys']) >= len(state['keys']):
            # Reset if enough time has passed (e.g., 24 hours) - simplified for now
            # logger.warning(f"All keys for {service} are exhausted.")
            # For now, just return the current one and hope for the best or rotate anyway
            pass
            
        current_key = state['keys'][state['current_index']]
        return current_key

    def report_error(self, service: str, key: str, error_code: int = 0):
        """Report an error with a specific key to trigger rotation.
        
        Args:
            service: Service name
            key: The key that failed
            error_code: HTTP status code or error type
        """
        service = service.upper()
        if service not in self.key_states:
            return
            
        state = self.key_states[service]
        
        # Only rotate on specific errors (Rate Limit, Forbidden, Quota Exceeded)
        if error_code in [429, 403, 401]:
            logger.warning(f"Key rotation triggered for {service} due to error {error_code}")
            self._rotate_key(service)
            
    def _rotate_key(self, service: str):
        """Switch to the next available key for a service."""
        state = self.key_states[service]
        total_keys = len(state['keys'])
        
        if total_keys <= 1:
            logger.warning(f"Cannot rotate key for {service}: only 1 key configured")
            return

        # Move to next index
        start_index = state['current_index']
        next_index = (start_index + 1) % total_keys
        
        state['current_index'] = next_index
        state['last_rotation'] = time.time()
        
        logger.info(f"Rotated {service} API key ({start_index+1}/{total_keys} -> {next_index+1}/{total_keys})")

# Global instance
_api_manager_instance: Optional[APIManager] = None

def get_api_manager() -> APIManager:
    """Get global API Manager instance."""
    global _api_manager_instance
    if _api_manager_instance is None:
        _api_manager_instance = APIManager()
    return _api_manager_instance
