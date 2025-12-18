"""
Facebook Module.
Scrapes friend lists and profiles using Playwright.
REQUIRES: FACEBOOK_EMAIL and FACEBOOK_PASSWORD in .env
"""
from loguru import logger
from core.engine import Profile
from config import get_config
from playwright.sync_api import sync_playwright
import time
import random

# Metadata
META = {
    'name': 'facebook',
    'description': 'Scrape Facebook Friend Lists (Authenticated)',
    'category': 'Social Media',
    'risk': 'high', # Risk of account ban
    'emoji': '📘'
}

def scan(target: str, profile: Profile):
    """
    Scrapes Facebook target (username/ID).
    Target format: 'username' or 'profile.php?id=...'
    """
    config = get_config()
    fb_email = config.get('FACEBOOK_EMAIL')
    fb_pass = config.get('FACEBOOK_PASSWORD')
    
    if not fb_email or not fb_pass:
        logger.error("[Facebook] Missing FACEBOOK_EMAIL or FACEBOOK_PASSWORD in .env")
        profile.add_error('facebook', 'Missing Credentials')
        return

    logger.info(f"[Facebook] Starting investigation on {target}...")

    try:
        with sync_playwright() as p:
            # Launch browser (headless=True usually, but FB might detect. 
            # Using firefox often helps avoiding detection)
            browser = p.firefox.launch(headless=True) 
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
            )
            page = context.new_page()
            
            # Login
            logger.info("[Facebook] Logging in...")
            page.goto("https://mbasic.facebook.com/") # Use mbasic for simpler parsing/speed
            
            if page.query_selector('input[name="email"]'):
                page.fill('input[name="email"]', fb_email)
                page.fill('input[name="pass"]', fb_pass)
                page.click('input[name="login"]')
                page.wait_for_timeout(3000)
                
            if "login_attempt" in page.url or "checkpoint" in page.url:
                logger.error("[Facebook] Login failed (Checkpoint/2FA triggered).")
                profile.add_error('facebook', 'Login Failed/Checkpoint')
                return
            
            logger.success("[Facebook] Login successful.")
            
            # Navigate to Target
            # Construct URL
            if target.isdigit():
                url = f"https://mbasic.facebook.com/profile.php?id={target}&v=friends"
            else:
                url = f"https://mbasic.facebook.com/{target}/friends"
                
            logger.info(f"[Facebook] Navigating to friend list: {url}")
            page.goto(url)
            
            # Scrape Friends
            friends_found = []
            max_scroll = 5 # Safety limit for now
            
            for _ in range(max_scroll):
                # In mbasic, it's pagination via "See more friends" link usually
                # Extract current page friends
                # Selectors for mbasic friend names
                rows = page.query_selector_all('table.bm') # simplified selector assumption
                for row in rows:
                    text = row.inner_text()
                    if text:
                        friends_found.append(text.split('\n')[0]) # Name usually first line
                
                # Next page
                next_link = page.query_selector('a[href*="friends?unit_cursor"]') or \
                            page.query_selector('div#m_more_friends a')
                            
                if next_link:
                    next_link.click()
                    page.wait_for_timeout(random.randint(2000, 5000))
                else:
                    break
            
            count = len(friends_found)
            logger.success(f"[Facebook] Found {count} friends (sample).")
            profile.add_metadata({
                'facebook_friends_count': count,
                'facebook_friends_sample': friends_found[:50] # Store top 50
            })
            
            browser.close()

    except Exception as e:
        logger.error(f"[Facebook] Error: {e}")
        profile.add_error('facebook', str(e))
