"""
Leak Checker module for AthenaOSINT.

This module checks for data breaches using multiple APIs:
- Have I Been Pwned (HIBP)
- Dehashed
- Intelligence X
"""

import requests
import time
from typing import List, Dict, Any, Optional
from colorama import Fore, Style
from loguru import logger
from ratelimit import limits, sleep_and_retry

from config import get_config
from core.validators import validate_email


# Rate limiting: 1 request per second for HIBP free tier
@sleep_and_retry
@limits(calls=1, period=2)
def _rate_limited_request(url: str, headers: Dict[str, str]) -> requests.Response:
    """Make a rate-limited HTTP request.
    
    Args:
        url: URL to request
        headers: HTTP headers
        
    Returns:
        Response object
    """
    return requests.get(url, headers=headers, timeout=10)


def scan(target: str, profile) -> None:
    """Check for data breaches associated with an email.
    
    Args:
        target: Email address to check
        profile: Profile object to update with results
    """
    if not validate_email(target):
        logger.warning(f"Leak checker skipped - target '{target}' is not a valid email")
        return
    
    print(f"{Fore.CYAN}[+] Running Leak Checker module...{Style.RESET_ALL}")
    
    config = get_config()
    total_breaches = 0
    
    # Check HIBP
    hibp_breaches = _check_hibp(target, config)
    if hibp_breaches:
        for breach in hibp_breaches:
            profile.add_breach(breach)
        total_breaches += len(hibp_breaches)
    
    # Check Dehashed (if API key available)
    if config.has_api_key('DEHASHED'):
        dehashed_results = _check_dehashed(target, config)
        if dehashed_results:
            for breach in dehashed_results:
                profile.add_breach(breach)
            total_breaches += len(dehashed_results)
    
    
    # Check IntelX (if API key available)
    if config.has_api_key('INTELX'):
        intelx_results = _check_intelx(target, config)
        if intelx_results:
            for breach in intelx_results:
                profile.add_breach(breach)
            total_breaches += len(intelx_results)

    # 4. Check Local Vault (ALWAYS RUN - Free Mode)
    local_results = _check_local_vault(target)
    if local_results:
        for breach in local_results:
            profile.add_breach(breach)
        total_breaches += len(local_results)

    
    # Add email to profile
    if total_breaches > 0:
        profile.add_email(target)
    
    # Store results
    profile.raw_data['leak_checker'] = {
        'email': target,
        'total_breaches': total_breaches,
        'sources': {
            'hibp': len(hibp_breaches) if hibp_breaches else 0,
            'dehashed': len(dehashed_results) if 'dehashed_results' in locals() else 0,
            'intelx': len(intelx_results) if 'intelx_results' in locals() else 0,
            'local_vault': len(local_results)
        }
    }
    
    if total_breaches > 0:
        print(f"{Fore.RED}[!] Found {total_breaches} breach(es) for {target}{Style.RESET_ALL}")
        logger.warning(f"Leak checker found {total_breaches} breaches for {target}")
    else:
        print(f"{Fore.GREEN}[✓] No breaches found for {target}{Style.RESET_ALL}")
        logger.info(f"Leak checker: No breaches found for {target}")


def _check_hibp(email: str, config) -> List[Dict[str, Any]]:
    """Check Have I Been Pwned API.
    
    Args:
        email: Email to check
        config: Configuration object
        
    Returns:
        List of breach dictionaries
    """
    from core.api_manager import get_api_manager
    api_manager = get_api_manager()
    
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            api_key = api_manager.get_key('HIBP')
            
            headers = {
                'User-Agent': 'AthenaOSINT/1.0',
            }
            
            if api_key:
                headers['hibp-api-key'] = api_key
            else:
                logger.warning("HIBP: No API keys available")
                # Attempt without key or return empty? HIBP requires key now for most things
                # But let's try anyway or break
                pass
            
            url = f'https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false'
            
            if attempt == 0:
                print(f"  {Fore.CYAN}└─ Checking HIBP...{Style.RESET_ALL}")
            
            response = requests.get(url, headers=headers, timeout=10) # Using direct requests for simpler retry control
            
            if response.status_code == 200:
                breaches_data = response.json()
                breaches = []
                
                for breach in breaches_data:
                    breaches.append({
                        'source': 'HIBP',
                        'name': breach.get('Name', 'Unknown'),
                        'title': breach.get('Title', ''),
                        'date': breach.get('BreachDate', ''),
                        'description': breach.get('Description', ''),
                        'data_classes': breach.get('DataClasses', []),
                        'verified': breach.get('IsVerified', False),
                        'sensitive': breach.get('IsSensitive', False),
                        'domain': breach.get('Domain', ''),
                        'pwn_count': breach.get('PwnCount', 0)
                    })
                
                logger.info(f"HIBP: Found {len(breaches)} breaches")
                return breaches
                
            elif response.status_code == 404:
                logger.info(f"HIBP: No breaches found for {email}")
                return []
                
            elif response.status_code == 429: # Rate limit
                logger.warning(f"HIBP: Rate limit exceeded (Attempt {attempt+1}/{max_retries})")
                if api_key:
                    api_manager.report_error('HIBP', api_key, 429)
                time.sleep(2) # Wait a bit before retry
                continue 
                
            elif response.status_code == 401: # Unauthorized (Bad key)
                logger.warning(f"HIBP: Invalid API key (Attempt {attempt+1}/{max_retries})")
                if api_key:
                    api_manager.report_error('HIBP', api_key, 401)
                continue
                
            else:
                logger.error(f"HIBP: API returned {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"HIBP check failed: {e}")
            return []
            
    return []


def _check_dehashed(email: str, config) -> List[Dict[str, Any]]:
    """Check Dehashed API.
    
    Args:
        email: Email to check
        config: Configuration object
        
    Returns:
        List of breach dictionaries
    """
    try:
        api_key = config.get('DEHASHED_API_KEY')
        username = config.get('DEHASHED_USERNAME')
        
        if not api_key or not username:
            logger.debug("Dehashed: API credentials not configured")
            return []
        
        headers = {
            'Accept': 'application/json',
        }
        
        url = f'https://api.dehashed.com/search?query=email:{email}'
        
        print(f"  {Fore.CYAN}└─ Checking Dehashed...{Style.RESET_ALL}")
        
        response = requests.get(
            url,
            headers=headers,
            auth=(username, api_key),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            entries = data.get('entries', [])
            
            breaches = []
            for entry in entries:
                breaches.append({
                    'source': 'Dehashed',
                    'name': entry.get('database_name', 'Unknown'),
                    'date': entry.get('obtained_from', ''),
                    'email': entry.get('email', ''),
                    'username': entry.get('username', ''),
                    'password': entry.get('password', '[REDACTED]'),
                    'hashed_password': entry.get('hashed_password', ''),
                    'ip_address': entry.get('ip_address', ''),
                    'data_classes': ['Email', 'Password'] if entry.get('password') else ['Email']
                })
            
            logger.info(f"Dehashed: Found {len(breaches)} entries")
            return breaches
        else:
            logger.error(f"Dehashed: API returned {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Dehashed check failed: {e}")
        return []


def _check_intelx(email: str, config) -> List[Dict[str, Any]]:
    """Check Intelligence X API.
    
    Args:
        email: Email to check
        config: Configuration object
        
    Returns:
        List of breach dictionaries
    """
    try:
        api_key = config.get('INTELX_API_KEY')
        
        if not api_key:
            logger.debug("IntelX: API key not configured")
            return []
        
        headers = {
            'x-key': api_key,
            'Content-Type': 'application/json'
        }
        
        # Initiate search
        search_url = 'https://2.intelx.io/intelligent/search'
        search_payload = {
            'term': email,
            'maxresults': 100,
            'media': 0,
            'sort': 4
        }
        
        print(f"  {Fore.CYAN}└─ Checking IntelX...{Style.RESET_ALL}")
        
        response = requests.post(
            search_url,
            json=search_payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            search_data = response.json()
            search_id = search_data.get('id')
            
            if not search_id:
                return []
            
            # Wait for results
            time.sleep(2)
            
            # Get results
            results_url = f'https://2.intelx.io/intelligent/search/result?id={search_id}'
            results_response = requests.get(results_url, headers=headers, timeout=10)
            
            if results_response.status_code == 200:
                results = results_response.json()
                records = results.get('records', [])
                
                breaches = []
                for record in records:
                    breaches.append({
                        'source': 'IntelX',
                        'name': record.get('name', 'Unknown'),
                        'date': record.get('date', ''),
                        'type': record.get('type', ''),
                        'bucket': record.get('bucket', ''),
                        'data_classes': ['Leaked Data']
                    })
                
                logger.info(f"IntelX: Found {len(breaches)} records")
                return breaches
            else:
                logger.error(f"IntelX: Results API returned {results_response.status_code}")
                return []
        else:
            logger.error(f"IntelX: Search API returned {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"IntelX check failed: {e}")
        return []


def check_password_paste(password_hash: str) -> bool:
    """Check if a password hash appears in pastes.
    
    Args:
        password_hash: SHA-1 hash of password (first 5 chars)
        
    Returns:
        True if found in pastes
    """
    try:
        # HIBP Pwned Passwords API
        url = f'https://api.pwnedpasswords.com/range/{password_hash[:5]}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            hashes = response.text.split('\n')
            suffix = password_hash[5:].upper()
            
            for hash_line in hashes:
                if hash_line.startswith(suffix):
                    return True
        
        return False
        
    except Exception as e:
        logger.error(f"Password paste check failed: {e}")
        return False


def _check_local_vault(target: str) -> List[Dict[str, Any]]:
    """Check local processed breach files for the target.
    
    Args:
        target: Email/Username to check
        
    Returns:
        List of breach findings
    """
    from pathlib import Path
    import os
    
    PROCESSED_DIR = Path("data/processed")
    found_breaches = []
    
    if not PROCESSED_DIR.exists():
        return []
        
    print(f"  {Fore.CYAN}└─ Checking Local Breach Vault...{Style.RESET_ALL}")
    
    try:
        # Search all cleaned files
        for file_path in PROCESSED_DIR.glob("clean_*"):
            try:
                # Use Grep for speed (if on linux) or simple python read
                # Python read line by line efficiently
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if target in line:
                            # Parse credential
                            try:
                                parts = line.strip().split(':', 1)
                                if len(parts) == 2:
                                    user, password = parts
                                    if user == target:
                                         found_breaches.append({
                                            'source': 'Local Vault',
                                            'name': file_path.name.replace('clean_', ''),
                                            'date': time.strftime('%Y-%m-%d', time.gmtime(os.path.getmtime(file_path))),
                                            'title': 'Local Breach Data',
                                            'description': f'Found in {file_path.name} line {line_num}',
                                            'password': password,  # We found the password
                                            'data_classes': ['Email', 'Password']
                                        })
                            except:
                                continue
            except Exception as fe:
                continue
                
        if found_breaches:
            logger.info(f"Local Vault: Found {len(found_breaches)} hits")
        
        return found_breaches
        
    except Exception as e:
        logger.error(f"Local vault check failed: {e}")
        return []

