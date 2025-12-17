"""
DNSDumpster module for AthenaOSINT.

This module retrieves DNS records and network mapping data from DNSDumpster.
"""

import requests
import re
from typing import Dict, List, Any
from colorama import Fore, Style
from loguru import logger
from bs4 import BeautifulSoup

from core.engine import Profile

def scan(target: str, profile: Profile) -> None:
    """Scan a domain using DNSDumpster.
    
    Args:
        target: Domain to scan
        profile: Profile object to update
    """
    # Only run on domains
    if '@' in target or not '.' in target:
        return

    print(f"{Fore.CYAN}[+] Running DNSDumpster module...{Style.RESET_ALL}")
    
    try:
        session = requests.Session()
        session.headers.update({
             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
             'Referer': 'https://dnsdumpster.com/'
        })

        # Get CSRF token
        url = 'https://dnsdumpster.com/'
        req = session.get(url)
        soup = BeautifulSoup(req.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

        # Post lookup
        data = {
            'csrfmiddlewaretoken': csrf_token,
            'targetip': target,
            'user': 'free'
        }
        
        post_req = session.post(url, data=data, headers={'Referer': url})
        
        if post_req.status_code != 200:
            logger.error(f"DNSDumpster returned {post_req.status_code}")
            return

        soup = BeautifulSoup(post_req.content, 'html.parser')
        tables = soup.find_all('table')
        
        findings = {
            'dns': [],
            'mx': [],
            'txt': [],
            'host': []
        }

        if not tables:
            print(f"{Fore.YELLOW}[!] No results found on DNSDumpster{Style.RESET_ALL}")
            return

        # Simple parsing of the tables
        # Usually: 0=DNS, 1=MX, 2=TXT, 3=Host (A)
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if not cols:
                    continue
                    
                # Extract data based on structure (simplified)
                # Text usually contains domain/ip
                text_content = [c.get_text(strip=True) for c in cols]
                
                # Check for IPs
                ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', str(row))
                for ip in ips:
                    profile.add_ip(ip)

                # Check for subdomains
                # Many cols have 'sub.domain.com'
                for col in cols:
                    possible_domains = col.get_text().split()
                    for item in possible_domains:
                        if target in item and '.' in item:
                            clean_domain = item.strip().strip('()[]')
                            if clean_domain != target:
                                profile.add_subdomain(clean_domain)
        
        # Store raw map image link if found
        map_img = soup.find('img', {'class': 'img-responsive'})
        if map_img and 'src' in map_img.attrs:
            map_url = 'https://dnsdumpster.com' + map_img['src']
            findings['map_url'] = map_url
            profile.raw_data.setdefault('dnsdumpster', {})['map_url'] = map_url
            print(f"  {Fore.GREEN}└─ Found Network Map: {map_url}{Style.RESET_ALL}")

        count_subs = len(profile.subdomains)
        print(f"{Fore.GREEN}[✓] DNSDumpster analysis complete{Style.RESET_ALL}")
        logger.info(f"DNSDumpster: Found network map and updated subdomains")

    except Exception as e:
        logger.error(f"DNSDumpster scan failed: {e}")
        print(f"{Fore.RED}[!] DNSDumpster scan failed: {e}{Style.RESET_ALL}")
