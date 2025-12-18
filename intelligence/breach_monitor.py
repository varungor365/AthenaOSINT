#!/usr/bin/env python3
"""
Autonomous Breach Database Monitor

Continuously monitors and downloads publicly available breach databases,
leaked credentials, and combo lists from various sources.
"""

import asyncio
import hashlib
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from urllib.parse import urlparse
import aiohttp
from playwright.async_api import async_playwright, Browser, Page
from loguru import logger
import magic
from config import get_config


class BreachMonitor:
    """Monitors and downloads breach databases autonomously."""
    
    # Public breach aggregators and paste sites (legal, public sources)
    MONITORED_SOURCES = [
        {
            'name': 'HaveIBeenPwned Pastes',
            'url': 'https://haveibeenpwned.com/api/v3/breaches',
            'type': 'api',
            'interval': 3600  # Check hourly
        },
        {
            'name': 'Pastebin Recent',
            'url': 'https://pastebin.com/archive',
            'type': 'scrape',
            'interval': 1800  # Check every 30 mins
        },
        {
            'name': 'GitHub Gists',
            'url': 'https://gist.github.com/discover',
            'type': 'scrape',
            'interval': 3600
        },
        {
            'name': 'Ghostbin',
            'url': 'https://ghostbin.com/browse',
            'type': 'scrape',
            'interval': 3600
        },
        {
            'name': 'Rentry.co',
            'url': 'https://rentry.co/recent',
            'type': 'scrape',
            'interval': 1800
        }
    ]
    
    # Breach detection patterns
    BREACH_PATTERNS = [
        r'email.*password',
        r'\b[\w\.-]+@[\w\.-]+\.\w+\s*[:;|]\s*.+',  # email:password
        r'combo\s*list',
        r'leaked?\s*database',
        r'breach\s*dump',
        r'credential\s*dump'
    ]
    
    # Malware signatures to avoid
    MALWARE_EXTENSIONS = {'.exe', '.dll', '.scr', '.bat', '.cmd', '.vbs', '.ps1', '.msi', '.jar'}
    MALWARE_MIMES = {
        'application/x-msdownload',
        'application/x-dosexec',
        'application/x-executable',
        'application/octet-stream'
    }
    
    def __init__(self, data_dir: Path = None):
        """Initialize breach monitor."""
        self.config = get_config()
        self.data_dir = data_dir or Path("data/breach_vault")
        self.download_dir = self.data_dir / "downloads"
        self.processed_dir = self.data_dir / "processed"
        self.quarantine_dir = self.data_dir / "quarantine"
        
        # Create directories
        for dir_path in [self.download_dir, self.processed_dir, self.quarantine_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.browser: Optional[Browser] = None
        self.seen_hashes: Set[str] = set()
        self.last_check: Dict[str, datetime] = {}
        
        # Load seen hashes from disk
        self._load_seen_hashes()
        
        logger.info("BreachMonitor initialized")
    
    def _load_seen_hashes(self):
        """Load previously seen content hashes."""
        hash_file = self.data_dir / "seen_hashes.txt"
        if hash_file.exists():
            self.seen_hashes = set(hash_file.read_text().splitlines())
            logger.info(f"Loaded {len(self.seen_hashes)} seen content hashes")
    
    def _save_seen_hash(self, content_hash: str):
        """Save a content hash to prevent re-downloading."""
        self.seen_hashes.add(content_hash)
        hash_file = self.data_dir / "seen_hashes.txt"
        with hash_file.open('a') as f:
            f.write(f"{content_hash}\n")
    
    def _compute_hash(self, content: bytes) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content).hexdigest()
    
    def _is_breach_related(self, text: str) -> bool:
        """Check if text contains breach-related keywords."""
        text_lower = text.lower()
        for pattern in self.BREACH_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    def _is_safe_file(self, file_path: Path, content: bytes) -> bool:
        """Check if file is safe (not malware)."""
        # Check extension
        if file_path.suffix.lower() in self.MALWARE_EXTENSIONS:
            logger.warning(f"Blocked malware extension: {file_path.suffix}")
            return False
        
        # Check MIME type
        try:
            mime = magic.from_buffer(content, mime=True)
            if mime in self.MALWARE_MIMES:
                logger.warning(f"Blocked malware MIME type: {mime}")
                return False
        except Exception as e:
            logger.warning(f"Could not determine MIME type: {e}")
        
        # Check for executable signatures
        if content.startswith(b'MZ'):  # Windows executable
            logger.warning("Blocked Windows executable signature")
            return False
        
        if content.startswith(b'\x7fELF'):  # Linux executable
            logger.warning("Blocked Linux executable signature")
            return False
        
        return True
    
    async def _init_browser(self):
        """Initialize headless browser."""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            logger.info("Headless browser initialized")
    
    async def _close_browser(self):
        """Close headless browser."""
        if self.browser:
            await self.browser.close()
            self.browser = None
    
    async def scrape_pastebin(self) -> List[Dict]:
        """Scrape Pastebin for potential breaches."""
        findings = []
        
        try:
            await self._init_browser()
            page = await self.browser.new_page()
            await page.goto('https://pastebin.com/archive', wait_until='networkidle')
            
            # Get paste links
            paste_links = await page.query_selector_all('table.maintable a[href^="/"]')
            
            for link_elem in paste_links[:20]:  # Check latest 20 pastes
                try:
                    href = await link_elem.get_attribute('href')
                    if not href or href == '/':
                        continue
                    
                    paste_url = f'https://pastebin.com{href}'
                    
                    # Get raw content
                    raw_url = paste_url.replace('pastebin.com/', 'pastebin.com/raw/')
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(raw_url) as resp:
                            if resp.status == 200:
                                content = await resp.read()
                                text = content.decode('utf-8', errors='ignore')
                                
                                # Check if breach-related
                                if self._is_breach_related(text):
                                    content_hash = self._compute_hash(content)
                                    
                                    if content_hash not in self.seen_hashes:
                                        findings.append({
                                            'source': 'pastebin',
                                            'url': paste_url,
                                            'content': content,
                                            'hash': content_hash,
                                            'timestamp': datetime.utcnow()
                                        })
                                        logger.info(f"Found potential breach on Pastebin: {paste_url}")
                    
                    await asyncio.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error processing paste: {e}")
                    continue
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Pastebin scraping error: {e}")
        
        return findings
    
    async def scrape_gists(self) -> List[Dict]:
        """Scrape GitHub Gists for breach data."""
        findings = []
        
        try:
            await self._init_browser()
            page = await self.browser.new_page()
            
            # Search for common breach keywords
            keywords = ['combo list', 'email password', 'leaked database']
            
            for keyword in keywords:
                try:
                    search_url = f'https://gist.github.com/search?q={keyword.replace(" ", "+")}'
                    await page.goto(search_url, wait_until='networkidle')
                    
                    # Get gist links
                    gist_links = await page.query_selector_all('.gist-snippet-meta a.link-gray-dark')
                    
                    for link_elem in gist_links[:10]:  # Check top 10
                        try:
                            href = await link_elem.get_attribute('href')
                            if not href:
                                continue
                            
                            gist_url = f'https://gist.github.com{href}'
                            
                            # Get raw content
                            gist_id = href.split('/')[-1]
                            raw_url = f'https://gist.githubusercontent.com/{href}/raw'
                            
                            async with aiohttp.ClientSession() as session:
                                async with session.get(raw_url) as resp:
                                    if resp.status == 200:
                                        content = await resp.read()
                                        content_hash = self._compute_hash(content)
                                        
                                        if content_hash not in self.seen_hashes:
                                            findings.append({
                                                'source': 'github_gist',
                                                'url': gist_url,
                                                'content': content,
                                                'hash': content_hash,
                                                'timestamp': datetime.utcnow()
                                            })
                                            logger.info(f"Found potential breach in Gist: {gist_url}")
                            
                            await asyncio.sleep(2)
                            
                        except Exception as e:
                            logger.error(f"Error processing gist: {e}")
                            continue
                    
                    await asyncio.sleep(5)  # Rate limiting between searches
                    
                except Exception as e:
                    logger.error(f"Gist search error for '{keyword}': {e}")
                    continue
            
            await page.close()
            
        except Exception as e:
            logger.error(f"GitHub Gists scraping error: {e}")
        
        return findings
    
    async def check_hibp_breaches(self) -> List[Dict]:
        """Check HaveIBeenPwned for new breaches."""
        findings = []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'AthenaOSINT-BreachMonitor',
                }
                
                hibp_key = self.config.get('HIBP_API_KEY')
                if hibp_key:
                    headers['hibp-api-key'] = hibp_key
                
                async with session.get(
                    'https://haveibeenpwned.com/api/v3/breaches',
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        breaches = await resp.json()
                        
                        for breach in breaches:
                            breach_hash = hashlib.sha256(
                                breach['Name'].encode()
                            ).hexdigest()
                            
                            if breach_hash not in self.seen_hashes:
                                findings.append({
                                    'source': 'hibp',
                                    'breach_name': breach['Name'],
                                    'breach_date': breach.get('BreachDate'),
                                    'compromised_accounts': breach.get('PwnCount'),
                                    'data_classes': breach.get('DataClasses', []),
                                    'hash': breach_hash,
                                    'timestamp': datetime.utcnow()
                                })
                                logger.info(f"New HIBP breach: {breach['Name']}")
        
        except Exception as e:
            logger.error(f"HIBP API error: {e}")
        
        return findings
    
    async def download_finding(self, finding: Dict) -> Optional[Path]:
        """Download and validate a finding."""
        try:
            content = finding.get('content')
            if not content:
                return None
            
            # Generate filename
            timestamp = finding['timestamp'].strftime('%Y%m%d_%H%M%S')
            source = finding['source']
            filename = f"{source}_{timestamp}_{finding['hash'][:8]}.txt"
            file_path = self.download_dir / filename
            
            # Validate safety
            if not self._is_safe_file(file_path, content):
                # Quarantine suspicious file
                quarantine_path = self.quarantine_dir / filename
                quarantine_path.write_bytes(content)
                logger.warning(f"File quarantined: {quarantine_path}")
                return None
            
            # Save file
            file_path.write_bytes(content)
            self._save_seen_hash(finding['hash'])
            
            logger.info(f"Downloaded breach data: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    async def monitor_cycle(self):
        """Run one monitoring cycle."""
        logger.info("Starting breach monitoring cycle")
        
        all_findings = []
        
        # Check all sources
        all_findings.extend(await self.check_hibp_breaches())
        all_findings.extend(await self.scrape_pastebin())
        all_findings.extend(await self.scrape_gists())
        
        # Download new findings
        for finding in all_findings:
            await self.download_finding(finding)
            await asyncio.sleep(1)  # Rate limiting
        
        logger.info(f"Monitoring cycle complete. Found {len(all_findings)} new items.")
        return len(all_findings)
    
    async def run_forever(self, interval: int = 1800):
        """Run monitoring loop forever."""
        logger.info(f"Starting autonomous breach monitor (interval: {interval}s)")
        
        try:
            while True:
                try:
                    await self.monitor_cycle()
                except Exception as e:
                    logger.error(f"Monitor cycle error: {e}")
                
                logger.info(f"Sleeping for {interval}s...")
                await asyncio.sleep(interval)
        
        finally:
            await self._close_browser()


if __name__ == '__main__':
    monitor = BreachMonitor()
    asyncio.run(monitor.run_forever())
