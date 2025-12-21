"""
TheHarvester module for AthenaOSINT.

This module integrates theHarvester for email and domain reconnaissance.
"""

import subprocess
import re
from typing import List, Dict, Any
from colorama import Fore, Style
from loguru import logger

from core.validators import validate_domain, validate_email, extract_domain_from_email


def scan(target: str, profile) -> None:
    """Run theHarvester for domain/email intelligence.
    
    Args:
        target: Domain or email to investigate
        profile: Profile object to update with results
    """
    # Determine if target is domain or email
    if validate_email(target):
        domain = extract_domain_from_email(target)
        if not domain:
            logger.warning("Could not extract domain from email")
            return
        profile.add_email(target)
    elif validate_domain(target):
        domain = target
    else:
        logger.warning(f"TheHarvester skipped - invalid target: {target}")
        return
    
    print(f"{Fore.CYAN}[+] Running theHarvester module...{Style.RESET_ALL}")
    
    try:
        # Check if theHarvester is installed
        check_cmd = ['theHarvester', '--version']
        result = subprocess.run(
            check_cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            logger.warning("theHarvester not installed or not in PATH")
            profile.add_error('theharvester', 'Tool not installed')
            print(f"{Fore.YELLOW}[!] theHarvester not available{Style.RESET_ALL}")
            return
        
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"theHarvester check failed: {e}")
        profile.add_error('theharvester', 'Tool not available')
        print(f"{Fore.YELLOW}[!] theHarvester not available{Style.RESET_ALL}")
        return
    
    try:
        # Run theHarvester
        cmd = [
            'theHarvester',
            '-d', domain,
            '-b', 'all',   # All sources
            '-l', '2000'   # Increased limit for deep scan
        ]
        
        print(f"  {Fore.CYAN}└─ Scanning {domain}...{Style.RESET_ALL}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = f"theHarvester failed with exit code {result.returncode}"
            logger.error(error_msg)
            profile.add_error('theharvester', error_msg)
            return
        
        output = result.stdout
        
        # Parse output
        emails = _extract_emails(output)
        hosts = _extract_hosts(output)
        ips = _extract_ips(output)
        
        # Update profile
        for email in emails:
            profile.add_email(email)
        
        for host in hosts:
            if validate_domain(host):
                profile.add_subdomain(host)
        
        for ip in ips:
            profile.add_ip(ip)
        
        profile.add_domain(domain)
        
        # Store raw data
        profile.raw_data['theharvester'] = {
            'domain': domain,
            'emails_found': len(emails),
            'hosts_found': len(hosts),
            'ips_found': len(ips),
            'raw_output': output[:5000]  # Truncate for storage
        }
        
        print(f"{Fore.GREEN}[✓] theHarvester: {len(emails)} emails, {len(hosts)} hosts, {len(ips)} IPs{Style.RESET_ALL}")
        logger.info(f"theHarvester complete: {len(emails)} emails, {len(hosts)} hosts, {len(ips)} IPs")
        
    except subprocess.TimeoutExpired:
        error_msg = "theHarvester timed out after 2 minutes"
        logger.error(error_msg)
        profile.add_error('theharvester', error_msg)
        print(f"{Fore.RED}[✗] {error_msg}{Style.RESET_ALL}")
        
    except Exception as e:
        error_msg = f"theHarvester scan failed: {str(e)}"
        logger.error(error_msg)
        profile.add_error('theharvester', str(e))
        print(f"{Fore.RED}[✗] {error_msg}{Style.RESET_ALL}")


def _extract_emails(output: str) -> List[str]:
    """Extract email addresses from theHarvester output.
    
    Args:
        output: Command output
        
    Returns:
        List of unique email addresses
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, output)
    return list(set(emails))


def _extract_hosts(output: str) -> List[str]:
    """Extract hostnames from theHarvester output.
    
    Args:
        output: Command output
        
    Returns:
        List of unique hostnames
    """
    hosts = []
    
    # Look for hosts section
    if 'Hosts found' in output:
        hosts_section = output.split('Hosts found')[1]
        if '---' in hosts_section:
            hosts_section = hosts_section.split('---')[0]
        
        # Extract domain-like patterns
        domain_pattern = r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}'
        hosts = re.findall(domain_pattern, hosts_section)
    
    return list(set(hosts))


def _extract_ips(output: str) -> List[str]:
    """Extract IP addresses from theHarvester output.
    
    Args:
        output: Command output
        
    Returns:
        List of unique IP addresses
    """
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ips = re.findall(ip_pattern, output)
    
    # Filter out invalid IPs
    valid_ips = []
    for ip in ips:
        parts = ip.split('.')
        if all(0 <= int(part) <= 255 for part in parts):
            valid_ips.append(ip)
    
    return list(set(valid_ips))
