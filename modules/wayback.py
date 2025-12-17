"""
Wayback Machine module for AthenaOSINT.

This module checks the Internet Archive (Wayback Machine) for historical
snapshots of a target domain.
"""

import requests
from colorama import Fore, Style
from loguru import logger

from core.engine import Profile

def scan(target: str, profile: Profile) -> None:
    """Check Wayback Machine for snapshots.
    
    Args:
        target: Domain to check
        profile: Profile object
    """
    if '@' in target or '.' not in target:
        return # Domains only
        
    print(f"{Fore.CYAN}[+] Running Wayback Machine Check...{Style.RESET_ALL}")
    
    try:
        # CDX API
        url = f"http://web.archive.org/cdx/search/cdx?url={target}&output=json&limit=5"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # data[0] is header, rest are rows
            if len(data) > 1:
                snapshots = len(data) - 1
                latest = data[-1][1] # timestamp usually at index 1
                
                print(f"  {Fore.GREEN}└─ Found {snapshots} recent snapshots (Latest: {latest}){Style.RESET_ALL}")
                
                profile.raw_data['wayback'] = {
                    'found': True,
                    'snapshot_count': snapshots,
                    'latest_snapshot': latest,
                    'archive_url': f"https://web.archive.org/web/*/{target}"
                }
            else:
                print(f"  {Fore.YELLOW}└─ No snapshots found{Style.RESET_ALL}")
        else:
            logger.warning(f"Wayback API returned {response.status_code}")
            
    except Exception as e:
        logger.error(f"Wayback check failed: {e}")
