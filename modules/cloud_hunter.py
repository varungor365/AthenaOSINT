"""
Cloud Hunter module for AthenaOSINT.

This module actively searches for open cloud storage buckets
(AWS S3, Azure Blob, Google Cloud) matching the target name.
"""

import requests
import asyncio
import aiohttp
from colorama import Fore, Style
from loguru import logger

from core.engine import Profile

COMMON_BUCKET_PERMUTATIONS = [
    "{target}",
    "{target}-dev",
    "{target}-staging",
    "{target}-prod",
    "{target}-backup",
    "{target}-assets",
    "{target}-public",
    "www.{target}"
]

CLOUD_PROVIDERS = {
    'AWS': 'https://{bucket}.s3.amazonaws.com',
    'Google': 'https://storage.googleapis.com/{bucket}',
    'Azure': 'https://{bucket}.blob.core.windows.net/container' # Harder to guess without container
}

async def check_bucket(session, provider, url, profile_buckets):
    try:
        async with session.head(url, timeout=3) as resp:
            if resp.status in [200, 403]: # 200 = Open/Listable, 403 = Exists but protected
                status = "OPEN" if resp.status == 200 else "PROTECTED"
                color = Fore.RED if resp.status == 200 else Fore.YELLOW
                
                print(f"  {color}└─ [{status}] {provider}: {url}{Style.RESET_ALL}")
                
                profile_buckets.append({
                    'provider': provider,
                    'url': url,
                    'status': status
                })
    except:
        pass

async def run_checks(target_base, profile_buckets):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for fmt in COMMON_BUCKET_PERMUTATIONS:
            bucket_name = fmt.format(target=target_base)
            
            # AWS
            url = CLOUD_PROVIDERS['AWS'].format(bucket=bucket_name)
            tasks.append(check_bucket(session, 'AWS', url, profile_buckets))
            
            # Google
            url = CLOUD_PROVIDERS['Google'].format(bucket=bucket_name)
            tasks.append(check_bucket(session, 'Google', url, profile_buckets))
            
        await asyncio.gather(*tasks)

def scan(target: str, profile: Profile) -> None:
    """Scan for cloud buckets.
    
    Args:
        target: Target identifier (domain or username)
        profile: Profile object
    """
    print(f"{Fore.CYAN}[+] Running Cloud Hunter...{Style.RESET_ALL}")
    
    # Clean target for bucket names (remove TLDs if domain)
    if '.' in target:
        target_base = target.split('.')[0]
    else:
        target_base = target
        
    found_buckets = []
    
    # Run async checks
    try:
        # Check if we can run async in this context (usually yes if not in loop already)
        # For simplicity in this synchronous tool wrapper, we use asyncio.run
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_checks(target_base, found_buckets))
        
    except Exception as e:
        logger.error(f"Cloud Hunter failed: {e}")
    
    if found_buckets:
        profile.raw_data['cloud_assets'] = found_buckets
    else:
        print(f"  {Fore.YELLOW}└─ No cloud buckets found{Style.RESET_ALL}")
