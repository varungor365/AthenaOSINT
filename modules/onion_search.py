"""
OnionSearch Module.
Aggregates results from multiple Dark Web search engines (Ahmia, etc.).
Inspired by 'Darkdump' and 'OnionSearch' tools.
"""
from loguru import logger
from core.engine import Profile
import requests
from bs4 import BeautifulSoup

# Metadata
META = {
    'name': 'onion_search',
    'description': 'Dark Web Search Engine Aggregator',
    'category': 'Dark Web',
    'risk': 'medium',
    'emoji': '🧅'
}

def scan(target: str, profile: Profile):
    """
    Searches Ahmia and other accessible indexes for the target query.
    """
    logger.info(f"[OnionSearch] Searching for term: {target}")
    
    # 1. Ahmia.fi Search (Clearnet gateway to Darknet)
    try:
        url = f"https://ahmia.fi/search/?q={target}"
        res = requests.get(url, timeout=20)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            results = soup.select('li.result')
            
            count = 0
            for r in results[:15]: # Top 15
                try:
                    link_tag = r.find('a')
                    if not link_tag: continue
                    
                    link = link_tag['href']
                    text = link_tag.get_text().strip()
                    snippet_tag = r.find('p')
                    snippet = snippet_tag.get_text().strip() if snippet_tag else ""
                    
                    # Store finding
                    profile.add_metadata({
                        'source': 'ahmia',
                        'title': text,
                        'url': link,
                        'snippet': snippet
                    })
                    count += 1
                except:
                    continue
            
            if count > 0:
                logger.success(f"[OnionSearch] Found {count} results via Ahmia.")
            else:
                logger.warning("[OnionSearch] No results found on Ahmia.")
                
    except Exception as e:
        logger.error(f"[OnionSearch] Search failed: {e}")
        profile.add_error('onion_search', str(e))
