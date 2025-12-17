"""
Crypto Hunter module for AthenaOSINT.

This module scans text and profile data for Cryptocurrency addresses
(Bitcoin, Ethereum, Monero, etc.) and validates them.
"""

import re
from typing import List, Dict, Any
from colorama import Fore, Style
from loguru import logger

from core.engine import Profile

# Regex Definitions
CRYPTO_REGEX = {
    'BTC': r'\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b',
    'ETH': r'\b0x[a-fA-F0-9]{40}\b',
    'XMR': r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b',
    'DOGE': r'\bD{1}[5-9C-HJ-NP-U]{1}[1-9A-HJ-NP-Za-km-z]{32}\b'
}

def scan(target: str, profile: Profile) -> None:
    """Scan for crypto addresses in gathered data.
    
    Args:
        target: Target identifier
        profile: Profile object with raw_data populated
    """
    print(f"{Fore.CYAN}[+] Running Crypto Hunter...{Style.RESET_ALL}")
    
    found_wallets = []
    
    # Corpus to search: Bios, Metadata, maybe even raw HTML if we stored it
    # For now, we search in social bios and metadata
    corpus = []
    
    if 'social_details' in profile.raw_data:
        for site, details in profile.raw_data['social_details'].items():
            if details.get('bio'):
                corpus.append(f"{site}: {details['bio']}")
                
    # Search loop
    for text in corpus:
        for coin, pattern in CRYPTO_REGEX.items():
            matches = re.findall(pattern, text)
            for match in matches:
                # Basic check to avoid false positives (too common in hex strings for ETH)
                if coin == 'ETH' and '0x0000' in match: continue
                
                wallet = {
                    'coin': coin,
                    'address': match,
                    'source': text[:50] + "..." # truncated source
                }
                if wallet not in found_wallets:
                    found_wallets.append(wallet)
                    print(f"  {Fore.GREEN}└─ Found {coin} Wallet: {match[:10]}...{Style.RESET_ALL}")

    if found_wallets:
        profile.raw_data['crypto_wallets'] = found_wallets
        # Add to graph?
        # TODO: Add wallet nodes in graph update
    else:
        print(f"  {Fore.YELLOW}└─ No crypto addresses found{Style.RESET_ALL}")
