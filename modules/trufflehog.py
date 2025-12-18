"""
TruffleHog Module (Wrapper).
Scans for secrets, keys, and credentials in text or git repos.
Uses regex patterns similar to TruffleHog.
"""
import re
from loguru import logger
from core.engine import Profile

# Metadata
META = {
    'name': 'trufflehog',
    'description': 'Secret & Key Scanner',
    'category': 'Scanner',
    'risk': 'safe', 
    'emoji': '🐷'
}

# Simplified Regex patterns for common keys
PATTERNS = {
    'AWS Access Key': r'(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}',
    'Google API Key': r'AIza[0-9A-Za-z\\-_]{35}',
    'Slack Token': r'(xox[p|b|o|a]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-z0-9]{32})',
    'Private Key': r'-----BEGIN [A-Z]+ PRIVATE KEY-----',
    'Generic API Key': r'(?i)api_key[\s:=]+([a-zA-Z0-9]{32,45})'
}

def scan(target: str, profile: Profile):
    """
    Scans a target string (URL content or Repo URL) for secrets.
    For this module, if target is a URL, it fetches and parses.
    """
    logger.info(f"[TruffleHog] Scanning {target} for secrets...")
    
    content = ""
    
    # If target is HTTP, fetch it
    if target.startswith('http'):
        import requests
        try:
            res = requests.get(target, timeout=10)
            content = res.text
        except Exception as e:
            logger.error(f"[TruffleHog] Failed to fetch URL: {e}")
            return
    else:
        # Treat target as text to scan directly? Or maybe it's a file path?
        # For safety/simplicity in this context, we assume it's a value or we skip.
        # But commonly we might want to scan the *profile's accumulated text data*?
        # For now, let's just log.
        logger.warning("[TruffleHog] Target is not a URL. Skipping direct fetch.")
        return

    found_secrets = []
    
    for name, pattern in PATTERNS.items():
        matches = re.findall(pattern, content)
        for match in matches:
            # Mask potential secret for logging
            masked = match[:4] + "*" * (len(match)-4)
            logger.warning(f"[TruffleHog] Found {name}: {masked}")
            found_secrets.append({
                'type': name,
                'value': match, # Store full value in secure profile (profile is internal)
                'masked': masked
            })
            
    if found_secrets:
        logger.success(f"[TruffleHog] Found {len(found_secrets)} potential secrets!")
        profile.add_metadata({'secrets_found': found_secrets})
    else:
        logger.info("[TruffleHog] No secrets found in public response.")
