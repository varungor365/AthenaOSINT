"""
WitnessMe Module.
Automated screenshot of profiles/sites using Playwright.
Equivalent to EyeWitness/WitnessMe tools.
"""
from loguru import logger
from core.engine import Profile
from playwright.sync_api import sync_playwright
import os
from pathlib import Path
from config import get_config

# Metadata
META = {
    'name': 'witnessme',
    'description': 'Automated Website Screenshotter',
    'category': 'Utils',
    'risk': 'safe', 
    'emoji': '📸'
}

def scan(target: str, profile: Profile):
    """
    Takes a screenshot of the target URL.
    """
    if not target.startswith('http'):
        target = 'https://' + target

    logger.info(f"[WitnessMe] Capturing screenshot for {target}...")

    config = get_config()
    data_dir = config.get('REPORTS_DIR') # Save in reports/screenshots ideally
    screenshot_dir = data_dir / 'screenshots'
    screenshot_dir.mkdir(exist_ok=True, parents=True) # Ensure dir exists

    filename = target.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '') + '.png'
    save_path = screenshot_dir / filename

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Set viewport
            page.set_viewport_size({"width": 1280, "height": 720})
            
            try:
                page.goto(target, timeout=15000)
                page.wait_for_timeout(2000) # Wait for animations
                
                # Full page or view? witnessme usually does full page or specific elements
                page.screenshot(path=str(save_path))
                
                logger.success(f"[WitnessMe] Screenshot saved to {save_path}")
                profile.add_metadata({'screenshot': str(save_path)})
                
            except Exception as e:
                logger.warning(f"[WitnessMe] Page load failed: {e}")
                
            browser.close()

    except Exception as e:
        logger.error(f"[WitnessMe] Engine error: {e}")
        profile.add_error('witnessme', str(e))
