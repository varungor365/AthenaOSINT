"""
TorBot Module.
Crawls .onion links to map structure and gather intelligence.
Requires Tor proxy (usually localhost:9050).
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from loguru import logger
from core.engine import Profile

# Metadata
META = {
    'name': 'torbot',
    'description': 'Dark Web Crawler (.onion)',
    'category': 'Dark Web',
    'risk': 'high', # connect to dark web
    'emoji': '🤖'
}

def scan(target: str, profile: Profile):
    """
    Crawls a .onion URL.
    """
    if '.onion' not in target:
        logger.info("[TorBot] Target is not an .onion link. Skipping.")
        return

    # Tor Proxy Configuration
    # Ensure Socks5 proxy is running (default Tor port)
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    
    logger.info(f"[TorBot] Starting crawl on {target} via Tor...")
    
    visited = set()
    queue = [target]
    max_pages = 20 # Safety limit
    
    while queue and len(visited) < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
            
        try:
            # Requires 'requests[socks]' installed
            res = requests.get(url, proxies=proxies, timeout=30)
            visited.add(url)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                title = soup.title.string if soup.title else "No Title"
                logger.info(f"  └─ [200] {title.strip()} ({url})")
                
                # Extract basic metadata
                profile.add_metadata({'onion_title': title, 'url': url})
                
                # Extract Links for recursion
                for a in soup.find_all('a', href=True):
                    link = urljoin(url, a['href'])
                    if '.onion' in link and link not in visited:
                        queue.append(link)
                        
        except Exception as e:
            # Allow graceful failure if Tor is not running
            logger.error(f"[TorBot] Failed to crawl (Ensure Tor is running): {e}")
            profile.add_error('torbot', str(e))
            break
            
    logger.success(f"[TorBot] Crawl complete. Visited {len(visited)} pages.")
