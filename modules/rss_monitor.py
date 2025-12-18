"""
RSS Monitor Module.
Fetches articles from RSS feeds (Medium, Blogs) for intelligence gathering.
Inspired by 'Writeup-Miner'.
"""
import requests
import feedparser # We might need to add this to requirements, or use simple xml parsing
from loguru import logger
from core.engine import Profile

# Metadata
META = {
    'name': 'rss_monitor',
    'description': 'RSS Feed Monitor (Medium/Blogs)',
    'category': 'Automation',
    'risk': 'safe', 
    'emoji': '📰'
}

def scan(target: str, profile: Profile):
    """
    Fetches RSS feed for a target (user or custom URL).
    If target is a username, assumes Medium.
    """
    url = target
    if not target.startswith('http'):
        # Assume medium username
        url = f"https://medium.com/feed/@{target}"
        
    logger.info(f"[RSS] Fetching feed: {url}")
    
    try:
        # Simple text fetch first
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            logger.warning(f"[RSS] Failed to fetch feed (Status: {res.status_code})")
            return

        # Simple XML parsing (avoiding extra dependency if possible, but feedparser is standard)
        # We'll use simple string checks for now to be dependency-lite, or assume lxml is present
        
        # Taking a shortcut: Just extracting titles/links via regex/soup for robustness
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, 'xml')
        
        items = soup.find_all('item')
        if not items:
            items = soup.find_all('entry') # Atom
            
        count = 0
        for item in items:
            if count >= 10: break
            
            title = item.find('title')
            link = item.find('link')
            pubDate = item.find('pubDate') or item.find('published')
            
            t_text = title.text if title else "No Title"
            l_text = link.text if link else (link.get('href') if link else "")
            d_text = pubDate.text if pubDate else ""
            
            profile.add_metadata({
                'rss_article': {
                    'title': t_text,
                    'link': l_text,
                    'date': d_text
                }
            })
            count += 1
            
        logger.success(f"[RSS] Retrieved {count} articles.")

    except Exception as e:
        logger.error(f"[RSS] Error: {e}")
        profile.add_error('rss_monitor', str(e))
