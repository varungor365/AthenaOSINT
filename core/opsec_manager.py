"""
OpSec Manager.
Handles Operations Security: Header Spoofing, Jitter, and Proxy Logic.
"""

import time
import random
from typing import Dict, Optional
from loguru import logger
from colorama import Fore, Style

# Common User Agents (Chrome, Firefox, Safari on Windows/Mac/Linux)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
]

class OpSecManager:
    """Manages stealth and operational security."""
    
    def __init__(self, low_and_slow: bool = False, smart_proxy: bool = False):
        self.low_and_slow = low_and_slow
        self.smart_proxy = smart_proxy
        self.current_user_agent = random.choice(USER_AGENTS)

    def get_headers(self) -> Dict[str, str]:
        """Get headers with spoofed fingerprint."""
        
        # Rotate UA occasionally? For now, sticky per session is better for consistency,
        # but random per request is harder to track. Let's do random per call if paranoid.
        
        ua = random.choice(USER_AGENTS)
        
        return {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

    def sleep_jitter(self, min_seconds: int = 1, max_seconds: int = 3) -> None:
        """Sleep for a random duration to mimic human behavior."""
        if self.low_and_slow:
            # Low and Slow mode: Wait significantly longer (e.g. 5-45s as requested)
            delay = random.uniform(5, 45)
            logger.info(f"Low-and-Slow: Sleeping for {delay:.2f}s...")
        else:
            # Normal jitter
            delay = random.uniform(min_seconds, max_seconds)
            
        time.sleep(delay)

    def get_proxy(self, target_domain: str = "") -> Optional[Dict[str, str]]:
        """Get a smart proxy based on target locale."""
        if not self.smart_proxy:
            return None
            
        # Geographic Heuristic Stub
        proxy = None
        
        if target_domain.endswith('.de'):
            # Return a German proxy if configured
            # proxy = "http://username:password@german-proxy-ip:port"
            pass
        elif target_domain.endswith('.ru'):
            # Return a Russian proxy?
            pass
        elif target_domain.endswith('.cn'):
            # Return China proxy?
            pass
            
        # For this implementation without paid proxy list, return None
        return proxy

