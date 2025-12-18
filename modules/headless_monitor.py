"""
Safe Headless Monitor.
Monitors specific, user-defined public URLs for intelligence.
NO recursive crawling. NO credential harvesting.
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from playwright.sync_api import sync_playwright, Browser, Page

logger = logging.getLogger("HeadlessMonitor")

RESULTS_DIR = Path("data/intelligence/monitor_results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

class SafeHeadlessMonitor:
    """
    Safely monitors public URLs using a headless browser.
    resource-constrained: Single page, strict timeouts.
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
                args=['--no-sandbox', '--disable-setuid-sandbox'] # Docker/Linux friendly
            )
        except Exception as e:
            logger.error(f"Failed to start headless browser: {e}")

    def check_url(self, url: str, keywords: List[str] = []) -> Dict:
        """
        Visit a single URL and check for keywords.
        Returns a summary of findings.
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
            'title': ''
        }
        
        try:
            context = self.browser.new_context(
                user_agent="AthenaOSINT-Monitor/1.0 (Safe Research Bot)"
            )
            page = context.new_page()
            
            # Strict timeout to save resources
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Content analysis
            title = page.title()
            content = page.content().lower()
            text_content = page.inner_text("body").lower()
            
            result['title'] = title
            result['status'] = 'success'
            
            # Check keywords relative to legitimate intelligence
            # (e.g., brand names, leak identifiers, but NOT specific personal data unless user defined)
            for kw in keywords:
                if kw.lower() in text_content:
                    result['matches'].append(kw)
            
            # Take screenshot if matches found
            if result['matches']:
                screenshot_path = RESULTS_DIR / f"evidence_{int(time.time())}.png"
                page.screenshot(path=str(screenshot_path))
                result['screenshot'] = str(screenshot_path)
                logger.info(f"Monitor hit on {url} for keywords: {result['matches']}")

                # Save JSON result
                self._save_result(result)
            
        except Exception as e:
            logger.warning(f"Monitor check failed for {url}: {e}")
            result['error'] = str(e)
            
        finally:
            if page:
                page.close()
            if context:
                context.close()
                
        return result

    def _save_result(self, result: Dict):
        """Save findings to disk."""
        try:
            filename = f"monitor_{int(time.time())}.json"
            with open(RESULTS_DIR / filename, 'w') as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save monitor result: {e}")

    def close(self):
        """Cleanup resources."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

def run_monitor_loop(targets: List[Dict], interval: int = 3600):
    """
    Simple loop to run monitor checks.
    targets: [{'url': '...', 'keywords': [...]}]
    """
    monitor = SafeHeadlessMonitor()
    try:
        while True:
            logger.info("Starting monitor cycle...")
            for target in targets:
                monitor.check_url(target['url'], target.get('keywords', []))
                time.sleep(5) # Polite delay between requests
            
            logger.info(f"Monitor cycle complete. Sleeping for {interval}s")
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Monitor loop stopped.")
    finally:
        monitor.close()
