"""
Canary Checker Module.
Detects CanaryTokens, Honeytokens, and tracking pixels in URLs/Files.
"""

from typing import List, Dict, Any
from colorama import Fore, Style
from core.engine import Profile

META = {
    'description': 'Detects CanaryTokens and tracking links',
    'target_type': 'url, file',
    'requirements': 'None'
}

KNOWN_CANARY_DOMAINS = [
    "canarytokens.com",
    "canarytokens.org",
    "interact.sh", # ProjectDiscovery interactsh
    "burpcollaborator.net",
    "oast.pro",
    "oast.live",
    "oast.site",
    "oast.online",
    "oast.fun",
    "oast.me",
    "requestbin.net",
    "dnslog.cn"
]

def scan(target: str, profile: Profile) -> None:
    """Run Canary Checker on target or profile data."""
    print(f"{Fore.CYAN}[+] Running Canary/Honeytoken Checker...{Style.RESET_ALL}")
    
    found_tokens = []
    
    # 1. Check if the target itself is a token (if it's a domain/url)
    for domain in KNOWN_CANARY_DOMAINS:
        if domain in target:
            print(f"  {Fore.RED}⚠ WARNING: Target '{target}' appears to be a CanaryToken/Honeytoken!{Style.RESET_ALL}")
            found_tokens.append({'source': 'target_input', 'token': target, 'type': 'Domain Match'})
            
    # 2. Check gathered URLs in profile
    # (Assuming other modules populated raw_data['urls'] or similar)
    # We'll check 'domains' and raw_data values used in other modules
    
    corpus = []
    if hasattr(profile, 'domains'):
        corpus.extend(profile.domains)
    
    # Also check generic raw text if available?
    
    for item in corpus:
        for domain in KNOWN_CANARY_DOMAINS:
            if domain in str(item):
                 print(f"  {Fore.RED}⚠ WARNING: Found potential Honeytoken: {item}{Style.RESET_ALL}")
                 found_tokens.append({'source': 'discovered_data', 'token': item, 'type': 'related_domain'})

    if found_tokens:
        profile.raw_data.setdefault('alerts', []).extend(found_tokens)
        print(f"  {Fore.RED}└─ DETECTED {len(found_tokens)} POTENTIAL HONEYTOKENS. EXERCISE CAUTION.{Style.RESET_ALL}")
    else:
        print(f"  {Fore.GREEN}└─ No obvious honeytokens detected in target/profile.{Style.RESET_ALL}")

