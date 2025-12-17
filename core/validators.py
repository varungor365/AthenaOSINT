"""
Input validation utilities for AthenaOSINT.

This module provides functions to validate and detect various types
of OSINT targets (emails, usernames, domains, IPs, phone numbers).
"""

import re
from typing import Optional
from urllib.parse import urlparse


def validate_email(email: str) -> bool:
    """Validate an email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_domain(domain: str) -> bool:
    """Validate a domain name.
    
    Args:
        domain: Domain name to validate
        
    Returns:
        True if valid domain format, False otherwise
    """
    # Remove protocol if present
    if '://' in domain:
        parsed = urlparse(domain)
        domain = parsed.netloc or parsed.path
    
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


def validate_username(username: str) -> bool:
    """Validate a username.
    
    Args:
        username: Username to validate
        
    Returns:
        True if valid username format, False otherwise
    """
    # Allow alphanumeric, underscores, hyphens, dots
    # Length between 3-30 characters
    pattern = r'^[a-zA-Z0-9._-]{3,30}$'
    return bool(re.match(pattern, username))


def validate_ip(ip: str) -> bool:
    """Validate an IPv4 or IPv6 address.
    
    Args:
        ip: IP address to validate
        
    Returns:
        True if valid IP format, False otherwise
    """
    # IPv4 pattern
    ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    
    # IPv6 pattern (simplified)
    ipv6_pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    
    return bool(re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip))


def validate_phone(phone: str) -> bool:
    """Validate a phone number.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid phone format, False otherwise
    """
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    
    # Check if it starts with + and has 10-15 digits
    pattern = r'^\+?[1-9]\d{9,14}$'
    return bool(re.match(pattern, cleaned))


def validate_target(target: str) -> bool:
    """Validate any supported target type.
    
    Args:
        target: Target to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not target or not isinstance(target, str):
        return False
    
    target = target.strip()
    
    return (
        validate_email(target) or
        validate_domain(target) or
        validate_username(target) or
        validate_ip(target) or
        validate_phone(target)
    )


def detect_target_type(target: str) -> Optional[str]:
    """Detect the type of a target.
    
    Args:
        target: Target to analyze
        
    Returns:
        Target type as string ('email', 'domain', 'username', 'ip', 'phone')
        or None if not recognized
    """
    if not target:
        return None
    
    target = target.strip()
    
    if validate_email(target):
        return 'email'
    elif validate_ip(target):
        return 'ip'
    elif validate_phone(target):
        return 'phone'
    elif validate_domain(target):
        return 'domain'
    elif validate_username(target):
        return 'username'
    else:
        return 'unknown'


def normalize_target(target: str) -> str:
    """Normalize a target for consistent processing.
    
    Args:
        target: Target to normalize
        
    Returns:
        Normalized target string
    """
    if not target:
        return ''
    
    target = target.strip().lower()
    
    # Remove protocol from URLs/domains
    if '://' in target:
        parsed = urlparse(target)
        target = parsed.netloc or parsed.path
    
    # Normalize phone numbers
    if validate_phone(target):
        target = re.sub(r'[\s\-\(\)\.]', '', target)
    
    return target


def extract_domain_from_email(email: str) -> Optional[str]:
    """Extract domain from email address.
    
    Args:
        email: Email address
        
    Returns:
        Domain part of email or None
    """
    if not validate_email(email):
        return None
    
    return email.split('@')[1]


def is_disposable_email(email: str) -> bool:
    """Check if an email uses a disposable email service.
    
    Args:
        email: Email address to check
        
    Returns:
        True if likely disposable, False otherwise
    """
    disposable_domains = {
        'tempmail.com', '10minutemail.com', 'guerrillamail.com',
        'mailinator.com', 'trash-mail.com', 'throwaway.email',
        'temp-mail.org', 'fakeinbox.com', 'yopmail.com',
        'getnada.com', 'trashmail.com', 'maildrop.cc'
    }
    
    if not validate_email(email):
        return False
    
    domain = extract_domain_from_email(email)
    return domain in disposable_domains if domain else False
