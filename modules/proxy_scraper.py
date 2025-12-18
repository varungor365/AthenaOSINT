"""
Proxy Scraper Module.
Harvests free proxies (HTTP/Socks) from public sources.
Inspired by 'uProxy'.
"""
import requests
import re
from loguru import logger
from core.engine import Profile

# Metadata
META = {
    'name': 'proxy_scraper',
    'description': 'Public Proxy Scraper (HTTP/SOCKS)',
    'category': 'Network',
    'risk': 'safe', 
    'emoji': '🛡️'
}

SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://www.proxy-list.download/api/v1/get?type=http",
    # Add more sources as needed
]

def scan(target: str, profile: Profile):
    """
    Scrapes proxies. Target arg is ignored (global tool), 
    but we can use it to filter country if we want.
    """
    logger.info("[ProxyScraper] Harvesting proxies...")
    
    unique_proxies = set()
    
    for source in SOURCES:
        try:
            res = requests.get(source, timeout=10)
            if res.status_code == 200:
                # Regex for IP:Port
                proxies = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', res.text)
                for p in proxies:
                    unique_proxies.add(p)
                logger.debug(f"[ProxyScraper] Got {len(proxies)} from {source}")
        except Exception as e:
            logger.warning(f"[ProxyScraper] Source {source} failed: {e}")
            
    count = len(unique_proxies)
    logger.success(f"[ProxyScraper] Harvested {count} unique proxies.")
    
    # Save to file or profile
    # For profile, we'll store a sample
    profile.add_metadata({'proxies_sample': list(unique_proxies)[:20], 'total_harvested': count})
    
    # Also save to data/proxies.txt
    from config import get_config
    data_dir = get_config().get('DATA_DIR')
    with open(data_dir / 'proxies.txt', 'w') as f:
        f.write('\n'.join(unique_proxies))
    logger.info(f"[ProxyScraper] Full list saved to {data_dir}/proxies.txt")
