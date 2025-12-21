"""
Safe Headless Monitor.
Monitors specific URLs for intelligence and CHANGE DETECTION (Diffing).
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import difflib

from playwright.sync_api import sync_playwright, Browser, Page

logger = logging.getLogger("HeadlessMonitor")

RESULTS_DIR = Path("data/intelligence/monitor_results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

class SafeHeadlessMonitor:
    """
    Safely monitors URLs and detects changes (Diffing).
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None
        self._start_browser()

    def _start_browser(self):
        """Initialize Playwright."""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
        except Exception as e:
            logger.error(f"Failed to start headless browser: {e}")

    def check_url(self, url: str, keywords: List[str] = []) -> Dict:
        """
        Visit a URL, check keywords, and compare with previous version.
        """
        if not self.browser:
            self._start_browser()
            if not self.browser:
                return {'error': 'Browser not available'}

        page: Optional[Page] = None
        result = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'status': 'failed',
            'matches': [],
            'change_detected': False,
            'diff_summary': ''
        }
        
        try:
            context = self.browser.new_context(
                user_agent="AthenaOSINT-Sentinel/2.0 (Safe Research Bot)"
            )
            page = context.new_page()
            
            # Visit
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Content
            text_content = page.inner_text("body")
            
            result['status'] = 'success'
            
            # 1. Keyword check
            for kw in keywords:
                if kw.lower() in text_content.lower():
                    result['matches'].append(kw)
            
            # 2. Diffing (Change Detection)
            prev_content = self._get_last_content(url)
            if prev_content:
                # Compare
                s = difflib.SequenceMatcher(None, prev_content, text_content)
                ratio = s.ratio()
                
                if ratio < 0.98: # If changed more than 2%
                    result['change_detected'] = True
                    result['diff_summary'] = f"Content changed by {(1-ratio)*100:.1f}%"
                    
                    # Log Evidence
                    screenshot_path = RESULTS_DIR / f"diff_{int(time.time())}.png"
                    page.screenshot(path=str(screenshot_path))
                    result['screenshot'] = str(screenshot_path)
                    logger.warning(f"SENTINEL: Change detected on {url} ({result['diff_summary']})")
            else:
                 logger.info(f"SENTINEL: First scan for {url}, saving baseline.")

            # Save current content for next time
            self._save_content_baseline(url, text_content)
            
            # Save findings
            self._save_result(result)
            
        except Exception as e:
            logger.warning(f"Monitor check failed for {url}: {e}")
            result['error'] = str(e)
            
        finally:
            if page: page.close()
            if context: context.close()
                
        return result

    def _get_hash(self, url):
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()

    def _get_last_content(self, url: str) -> Optional[str]:
        """Load last text content for this URL."""
        url_hash = self._get_hash(url)
        path = RESULTS_DIR / f"{url_hash}.txt"
        if path.exists():
            return path.read_text(encoding='utf-8')
        return None

    def _save_content_baseline(self, url: str, content: str):
        """Save text content as baseline."""
        url_hash = self._get_hash(url)
        path = RESULTS_DIR / f"{url_hash}.txt"
        path.write_text(content, encoding='utf-8')

    def _save_result(self, result: Dict):
        """Save findings."""
        if result.get('matches') or result.get('change_detected'):
            filename = f"monitor_alert_{int(time.time())}.json"
            with open(RESULTS_DIR / filename, 'w') as f:
                json.dump(result, f, indent=2)

    def close(self):
        """Cleanup."""
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()

# Wrapper for Engine call
def scan(target: str, profile):
    """
    Module entry point for the Engine.
    'target' is usually the URL to monitor.
    """
    monitor = SafeHeadlessMonitor()
    try:
        # We assume keywords might be in profile metadata or we use defaults
        # For simplicity, we search for generic risky keywords
        keywords = ["password", "leak", "sensitive", "confidential", "admin"]
        
        logger.info(f"Running Sentinel Check on {target}")
        result = monitor.check_url(target, keywords)
        
        if result['change_detected']:
            profile.add_pattern("Sentinel Alert", "high", f"Change Detected: {result['diff_summary']}")
        
        if result['matches']:
            profile.add_pattern("Sentinel Keyword", "medium", f"Found keywords: {result['matches']}")
            
        profile.add_metadata({'sentinel_result': result})
        
    finally:
        monitor.close()
