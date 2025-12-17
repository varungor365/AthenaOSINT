"""
Auto-Dorker module for AthenaOSINT.

This module generates and optionally executes Google Dorks to find
sensitive information, files, and login portals.
"""

from colorama import Fore, Style
from loguru import logger
import urllib.parse

from core.engine import Profile

def scan(target: str, profile: Profile) -> None:
    """Generate Dorks for the target.
    
    Args:
        target: Domain or username
        profile: Profile object
    """
    print(f"{Fore.CYAN}[+] Running Auto-Dorker...{Style.RESET_ALL}")
    
    dorks = []
    
    if '.' in target and '@' not in target:
        # Domain Dorks
        dorks = [
            f"site:{target} filetype:pdf",
            f"site:{target} filetype:xlsx",
            f"site:{target} filetype:docx",
            f"site:{target} inurl:admin",
            f"site:{target} inurl:login",
            f"site:{target} intitle:index.of",
            f"site:{target} \"password\"",
            f"site:github.com \"{target}\"",
            f"site:pastebin.com \"{target}\""
        ]
    else:
        # User/Email Dorks
        dorks = [
            f"\"{target}\" site:linkedin.com",
            f"\"{target}\" site:facebook.com",
            f"\"{target}\" site:instagram.com",
            f"\"{target}\" site:pastebin.com",
            f"\"{target}\" filetype:pdf" # Name in documents
        ]
        
    # Store dorks
    profile.raw_data['dorks'] = dorks
    
    print(f"  {Fore.GREEN}└─ Generated {len(dorks)} Google Dorks{Style.RESET_ALL}")
    
    # Verification/Execution? 
    # Automated searching of Google is blocked often. 
    # We will log them for the user "Narrative Report" or Dashboard.
    # We can try to run one or two if we had serpapi, but standard requests block.
    # Optimization: Just provide the links.
    
    for dork in dorks[:3]:
        encoded = urllib.parse.quote(dork)
        print(f"    - https://www.google.com/search?q={encoded}")
