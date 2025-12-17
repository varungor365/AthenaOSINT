"""
Subfinder module for AthenaOSINT.

This module integrates Subfinder for subdomain enumeration.
"""

import subprocess
import json
from typing import List
from colorama import Fore, Style
from loguru import logger

from core.validators import validate_domain


def scan(target: str, profile) -> None:
    """Run Subfinder for subdomain enumeration.
    
    Args:
        target: Domain to enumerate subdomains for
        profile: Profile object to update with results
    """
    if not validate_domain(target):
        logger.warning(f"Subfinder skipped - target '{target}' is not a valid domain")
        return
    
    print(f"{Fore.CYAN}[+] Running Subfinder module...{Style.RESET_ALL}")
    
    try:
        # Check if subfinder is installed
        check_cmd = ['subfinder', '-version']
        result = subprocess.run(
            check_cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            logger.warning("Subfinder not installed or not in PATH")
            profile.add_error('subfinder', 'Tool not installed')
            print(f"{Fore.YELLOW}[!] Subfinder not available{Style.RESET_ALL}")
            return
        
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"Subfinder check failed: {e}")
        profile.add_error('subfinder', 'Tool not available')
        print(f"{Fore.YELLOW}[!] Subfinder not available{Style.RESET_ALL}")
        return
    
    try:
        # Run Subfinder with JSON output
        cmd = [
            'subfinder',
            '-d', target,
            '-json',
            '-silent',
            '-all',  # Use all sources
            '-t', '50'  # 50 concurrent threads
        ]
        
        print(f"  {Fore.CYAN}└─ Enumerating subdomains for {target}...{Style.RESET_ALL}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = f"Subfinder failed with exit code {result.returncode}"
            logger.error(error_msg)
            profile.add_error('subfinder', error_msg)
            return
        
        output = result.stdout
        
        # Parse JSON output
        subdomains = []
        for line in output.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    subdomain = data.get('host', data.get('subdomain', ''))
                    if subdomain:
                        subdomains.append(subdomain)
                except json.JSONDecodeError:
                    # Fallback to plain text
                    if validate_domain(line.strip()):
                        subdomains.append(line.strip())
        
        # Update profile
        for subdomain in subdomains:
            profile.add_subdomain(subdomain)
        
        profile.add_domain(target)
        
        # Store raw data
        profile.raw_data['subfinder'] = {
            'domain': target,
            'subdomains_found': len(subdomains),
            'subdomains': subdomains[:100]  # Store first 100 for reference
        }
        
        print(f"{Fore.GREEN}[✓] Subfinder found {len(subdomains)} subdomains{Style.RESET_ALL}")
        logger.info(f"Subfinder complete: {len(subdomains)} subdomains found")
        
    except subprocess.TimeoutExpired:
        error_msg = "Subfinder timed out after 3 minutes"
        logger.error(error_msg)
        profile.add_error('subfinder', error_msg)
        print(f"{Fore.RED}[✗] {error_msg}{Style.RESET_ALL}")
        
    except Exception as e:
        error_msg = f"Subfinder scan failed: {str(e)}"
        logger.error(error_msg)
        profile.add_error('subfinder', str(e))
        print(f"{Fore.RED}[✗] {error_msg}{Style.RESET_ALL}")


def scan_passive_only(target: str, profile) -> None:
    """Run Subfinder in passive mode only (no active DNS queries).
    
    Args:
        target: Domain to enumerate
        profile: Profile object to update with results
    """
    if not validate_domain(target):
        return
    
    try:
        cmd = [
            'subfinder',
            '-d', target,
            '-json',
            '-silent',
            '-passive'  # Passive mode only
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            subdomains = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        subdomain = data.get('host', data.get('subdomain', ''))
                        if subdomain:
                            subdomains.append(subdomain)
                    except:
                        if validate_domain(line.strip()):
                            subdomains.append(line.strip())
            
            for subdomain in subdomains:
                profile.add_subdomain(subdomain)
            
            logger.info(f"Subfinder passive: {len(subdomains)} subdomains")
        
    except Exception as e:
        logger.error(f"Subfinder passive scan failed: {e}")
