"""
Profile Scraper module for AthenaOSINT.

This module visits social media profile URLs discovered by other modules
to extract rich details like Bios, Pinned Links, Locations, and Avatars.
"""

import requests
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from colorama import Fore, Style
from loguru import logger

from core.engine import Profile

def scan(target: str, profile: Profile) -> None:
    """Scrape discovered profiles for more details.
    
    Args:
        target: Target identifier (unused here, we use profile.usernames)
        profile: Profile object to update
    """
    # This module works on EXISTING findings, so it should run after Sherlock/etc.
    if not profile.usernames:
        logger.debug("ProfileScraper: No usernames to scrape")
        return

    print(f"{Fore.CYAN}[+] Running Profile Scraper (Deep Analysis)...{Style.RESET_ALL}")
    
    scraped_count = 0
    
    # Iterate over found usernames/URLs
    # Note: profile.usernames is currently {platform: username}
    # We need to construct URLs or store URLs in profile.
    
    # We'll use a simple mapping for demo purposes. 
    # In a real app, Sherlock results should ideally store the full URL.
    # We'll check profile.raw_data['sherlock']['results'] if available.
    
    urls_to_scrape = []
    
    if 'sherlock' in profile.raw_data and 'results' in profile.raw_data['sherlock']:
        for site, data in profile.raw_data['sherlock']['results'].items():
            if data.get('status') == 'Claimed':
                urls_to_scrape.append((site, data.get('url')))
    else:
        # Fallback simplistic generation
        for platform, username in profile.usernames.items():
            if platform.lower() == 'twitter':
                urls_to_scrape.append(('Twitter', f'https://twitter.com/{username}'))
            elif platform.lower() == 'github':
                urls_to_scrape.append(('GitHub', f'https://github.com/{username}'))
            elif platform.lower() == 'instagram':
                urls_to_scrape.append(('Instagram', f'https://instagram.com/{username}'))

    # Headers to mimic browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for site, url in urls_to_scrape:
        if not url:
            continue
            
        print(f"  {Fore.CYAN}└─ Scraping {site}...{Style.RESET_ALL}", end='\r')
        
        try:
            # Special handling for sites might be needed (some block simple requests)
            # GitHub is easy to scrape:
            if site == 'GitHub':
                bio, location, links = _scrape_github(url, headers)
            elif site == 'Twitter':
                # Twitter is hard without API or Nitter. Skipping for now or using Nitter
                # url = url.replace('twitter.com', 'nitter.net')
                continue 
            else:
                # Generic fallback (meta description)
                bio, location, links = _scrape_generic(url, headers)
            
            if bio or location or links:
                scraped_count += 1
                # Store in profile
                if 'social_details' not in profile.raw_data:
                    profile.raw_data['social_details'] = {}
                
                profile.raw_data['social_details'][site] = {
                    'bio': bio,
                    'location': location,
                    'links': links
                }
                
                # If bio contains domains/emails, extract them
                if bio:
                    _extract_intel_from_text(bio, profile)
                
        except Exception as e:
            logger.debug(f"Failed to scrape {url}: {e}")
            continue

    if scraped_count > 0:
        print(f"  {Fore.GREEN}└─ Scraped details from {scraped_count} profiles{Style.RESET_ALL}")
    else:
        print(f"  {Fore.YELLOW}└─ No additional details scraped{Style.RESET_ALL}")

def _scrape_github(url: str, headers: Dict) -> tuple:
    """Specific scraper for GitHub."""
    resp = requests.get(url, headers=headers, timeout=5)
    if resp.status_code != 200:
        return None, None, None
        
    soup = BeautifulSoup(resp.content, 'html.parser')
    
    # Bio
    bio_div = soup.find('div', class_='p-note user-profile-bio')
    bio = bio_div.get_text(strip=True) if bio_div else None
    
    # Location
    loc_li = soup.find('li', itemprop='homeLocation')
    location = loc_li.get_text(strip=True) if loc_li else None
    
    # Website
    link_li = soup.find('li', itemprop='url')
    links = []
    if link_li:
        a = link_li.find('a')
        if a and a.get('href'):
            links.append(a['href'])
            
    return bio, location, links

def _scrape_generic(url: str, headers: Dict) -> tuple:
    """Generic scraper using finding meta tags."""
    resp = requests.get(url, headers=headers, timeout=5)
    if resp.status_code != 200:
        return None, None, None
        
    soup = BeautifulSoup(resp.content, 'html.parser')
    
    # Try meta description
    bio = None
    meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
    if meta_desc:
        bio = meta_desc.get('content', '').strip()
        
    return bio, None, []

def _extract_intel_from_text(text: str, profile: Profile):
    """Simple extraction of emails/domains from bio text."""
    # Emails
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    for email in emails:
        profile.add_email(email)
        
    # URLs -> Domains
    # Simplified regex for domain discovery
    # Don't grab twitter.com etc
    pass
