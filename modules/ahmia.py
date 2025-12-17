"""
Ahmia Module.
Scrapes Ahmia.fi for dark web results.
"""

import requests
from bs4 import BeautifulSoup
from core.engine import Profile

META = {
    'description': 'Dark Web Search Engine',
    'target_type': 'all'
}

def scan(target: str, profile: Profile) -> None:
    try:
        url = f"https://ahmia.fi/search/?q={target}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        results = []
        for li in soup.select('ul.searchResults li'):
             link = li.find('a')
             if link:
                 onion_url = link['href']
                 text = link.get_text(strip=True)
                 description = li.find('p').get_text(strip=True) if li.find('p') else ""
                 
                 results.append({'url': onion_url, 'title': text, 'snippet': description})
                 
        if results:
            profile.raw_data['darkweb_hits'] = results
            profile.add_pattern(f"Dark Web: {len(results)} hits", "high", "Found on Ahmia")
            
    except Exception as e:
        print(f"Ahmia error: {e}")
