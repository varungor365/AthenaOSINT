#!/usr/bin/env python3
"""
API Key Gatherer

Automatically discovers and gathers free API keys from public sources.
Tests and validates keys before adding to rotation pool.
"""

import asyncio
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from playwright.async_api import async_playwright, Browser
import aiohttp
from loguru import logger

from core.api_rotator import get_rotator


class APIGatherer:
    """Automatically gathers API keys from public sources."""
    
    # Public API directories and sources
    API_SOURCES = [
        {
            'name': 'Public APIs GitHub',
            'url': 'https://github.com/public-apis/public-apis',
            'type': 'github_readme'
        },
        {
            'name': 'RapidAPI',
            'url': 'https://rapidapi.com/collection/list-of-free-apis',
            'type': 'marketplace'
        },
        {
            'name': 'API List',
            'url': 'https://apilist.fun',
            'type': 'directory'
        }
    ]
    
    # Service signup URLs for auto-registration
    AUTO_SIGNUP_SERVICES = {
        'openweathermap': {
            'signup_url': 'https://home.openweathermap.org/users/sign_up',
            'api_key_path': 'https://home.openweathermap.org/api_keys',
            'test_endpoint': 'https://api.openweathermap.org/data/2.5/weather?q=London&appid={key}',
            'free_tier': True
        },
        'newsapi': {
            'signup_url': 'https://newsapi.org/register',
            'test_endpoint': 'https://newsapi.org/v2/top-headlines?country=us&apiKey={key}',
            'free_tier': True
        },
        'ipgeolocation': {
            'signup_url': 'https://ipgeolocation.io/signup.html',
            'test_endpoint': 'https://api.ipgeolocation.io/ipgeo?apiKey={key}',
            'free_tier': True
        },
        'exchangerate': {
            'signup_url': 'https://www.exchangerate-api.com',
            'test_endpoint': 'https://v6.exchangerate-api.com/v6/{key}/latest/USD',
            'free_tier': True
        },
        'nasa': {
            'signup_url': 'https://api.nasa.gov',
            'test_endpoint': 'https://api.nasa.gov/planetary/apod?api_key={key}',
            'free_tier': True,
            'demo_key': 'DEMO_KEY'  # NASA provides a demo key
        },
        'tmdb': {
            'signup_url': 'https://www.themoviedb.org/signup',
            'test_endpoint': 'https://api.themoviedb.org/3/movie/550?api_key={key}',
            'free_tier': True
        },
        'pexels': {
            'signup_url': 'https://www.pexels.com/api',
            'test_endpoint': 'https://api.pexels.com/v1/search?query=nature',
            'header_key': True,  # Uses Authorization header
            'free_tier': True
        },
        'unsplash': {
            'signup_url': 'https://unsplash.com/developers',
            'test_endpoint': 'https://api.unsplash.com/photos/?client_id={key}',
            'free_tier': True
        },
        'github': {
            'signup_url': 'https://github.com/settings/tokens',
            'test_endpoint': 'https://api.github.com/user',
            'header_key': True,
            'free_tier': True
        }
    }
    
    def __init__(self, browser: Browser = None):
        """Initialize API gatherer."""
        self.browser = browser
        self.rotator = get_rotator()
        self.discovered_keys = {}
        logger.info("APIGatherer initialized")
    
    async def _init_browser(self):
        """Initialize headless browser if needed."""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox']
            )
    
    async def test_api_key(self, service: str, key: str) -> bool:
        """Test if an API key is valid."""
        config = self.AUTO_SIGNUP_SERVICES.get(service)
        if not config or 'test_endpoint' not in config:
            return False
        
        try:
            endpoint = config['test_endpoint'].format(key=key)
            
            async with aiohttp.ClientSession() as session:
                headers = {}
                
                # Some APIs use header-based auth
                if config.get('header_key'):
                    headers['Authorization'] = f'Bearer {key}'
                    endpoint = config['test_endpoint']  # Don't format
                
                async with session.get(endpoint, headers=headers, timeout=10) as resp:
                    if resp.status in [200, 201]:
                        logger.info(f"✓ Valid API key for {service}")
                        return True
                    elif resp.status == 401 or resp.status == 403:
                        logger.warning(f"✗ Invalid API key for {service}")
                        return False
                    else:
                        logger.warning(f"? Unclear response for {service}: {resp.status}")
                        return False
        
        except Exception as e:
            logger.error(f"Error testing {service} key: {e}")
            return False
    
    async def gather_from_github_repos(self) -> List[Tuple[str, str]]:
        """Search GitHub for accidentally exposed API keys (educational purposes)."""
        # NOTE: This is for demonstration only - don't actually scrape private keys
        # Instead, focus on documented public demo keys
        
        known_demo_keys = [
            ('nasa', 'DEMO_KEY'),  # NASA's official demo key
        ]
        
        logger.info("Using known public demo keys")
        return known_demo_keys
    
    async def gather_from_public_docs(self) -> List[Tuple[str, str]]:
        """Gather API keys from public documentation."""
        discovered = []
        
        # Example patterns for demo keys in documentation
        demo_key_patterns = {
            'openweathermap': r'appid=([a-f0-9]{32})',
            'newsapi': r'apiKey=([a-f0-9]{32})',
            'github': r'token ([a-zA-Z0-9_]{40})',
        }
        
        # In a real implementation, you'd scrape official docs
        # For now, return empty to avoid false positives
        logger.info("Skipping public docs scraping (requires manual verification)")
        return discovered
    
    async def auto_register_service(self, service: str) -> Optional[str]:
        """
        Automatically register for a free API service.
        
        NOTE: This is a placeholder - actual implementation would need:
        1. Email generation/verification
        2. CAPTCHA solving
        3. Form automation
        
        For production, use manual registration or integrate with services
        that allow programmatic access.
        """
        logger.warning(f"Auto-registration not implemented for {service}")
        logger.info(f"Please manually register at: {self.AUTO_SIGNUP_SERVICES[service]['signup_url']}")
        return None
    
    async def discover_rapidapi_keys(self) -> List[Tuple[str, str]]:
        """Discover free tier API keys from RapidAPI marketplace."""
        discovered = []
        
        try:
            await self._init_browser()
            page = await self.browser.new_page()
            
            # Browse RapidAPI free APIs
            await page.goto('https://rapidapi.com/collection/list-of-free-apis')
            await page.wait_for_load_state('networkidle')
            
            # Extract API links
            api_links = await page.query_selector_all('a[href*="/api/"]')
            
            logger.info(f"Found {len(api_links)} APIs on RapidAPI")
            
            # Note: RapidAPI requires user signup, can't auto-gather keys
            # But we can identify which services are available
            
            await page.close()
        
        except Exception as e:
            logger.error(f"Error discovering RapidAPI keys: {e}")
        
        return discovered
    
    async def gather_all_keys(self) -> Dict[str, List[str]]:
        """Gather API keys from all sources."""
        logger.info("Starting API key gathering...")
        
        all_keys = {}
        
        # Gather from various sources
        github_keys = await self.gather_from_github_repos()
        docs_keys = await self.gather_from_public_docs()
        
        # Combine all discovered keys
        all_discovered = github_keys + docs_keys
        
        # Test and organize by service
        for service, key in all_discovered:
            if service not in all_keys:
                all_keys[service] = []
            
            # Test the key
            if await self.test_api_key(service, key):
                all_keys[service].append(key)
                
                # Add to rotator
                self.rotator.add_key(service, key, metadata={
                    'source': 'auto_discovered',
                    'discovered_at': datetime.utcnow().isoformat()
                })
        
        logger.info(f"Discovered {sum(len(v) for v in all_keys.values())} valid API keys")
        return all_keys
    
    def get_signup_instructions(self) -> List[Dict]:
        """Get manual signup instructions for all services."""
        instructions = []
        
        for service, config in self.AUTO_SIGNUP_SERVICES.items():
            instructions.append({
                'service': service,
                'signup_url': config['signup_url'],
                'free_tier': config.get('free_tier', False),
                'has_demo_key': 'demo_key' in config,
                'demo_key': config.get('demo_key')
            })
        
        return instructions
    
    async def validate_existing_keys(self):
        """Validate all existing keys in the rotator."""
        logger.info("Validating existing API keys...")
        
        for service in self.rotator.api_keys.keys():
            for key_data in self.rotator.api_keys[service]:
                key = key_data['key']
                
                if await self.test_api_key(service, key):
                    logger.info(f"✓ {service} key valid")
                else:
                    self.rotator.mark_key_failed(service, key, "Validation failed")
        
        logger.info("Key validation complete")


async def main():
    """Main gathering routine."""
    gatherer = APIGatherer()
    
    # Show signup instructions
    instructions = gatherer.get_signup_instructions()
    print("\n=== API Signup Instructions ===\n")
    for instr in instructions:
        print(f"Service: {instr['service']}")
        print(f"  Signup: {instr['signup_url']}")
        print(f"  Free Tier: {instr['free_tier']}")
        if instr['has_demo_key']:
            print(f"  Demo Key: {instr['demo_key']}")
        print()
    
    # Gather available keys
    keys = await gatherer.gather_all_keys()
    print(f"\nDiscovered {sum(len(v) for v in keys.values())} API keys")
    
    # Validate existing
    await gatherer.validate_existing_keys()


if __name__ == '__main__':
    asyncio.run(main())
