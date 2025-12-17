"""
OnionScan Lite.
Checks status of onion sites via Tor proxy (if available) or gateway.
"""

import requests
from core.engine import Profile

META = {
    'description': 'Check onion service health',
    'target_type': 'onion'
}

def scan(target: str, profile: Profile) -> None:
    # Just a stub unless Tor is configured
    # We can try to use a Tor2Web gateway for "Lite" check without local Tor
    
    gateway = f"https://{target}.onion.ly" # Common Tor2Web
    
    try:
        res = requests.head(gateway, timeout=10)
        status = 'Online' if res.status_code < 500 else 'Offline'
        
        result = {
            'target': target,
            'gateway_status': status,
            'server': res.headers.get('Server', 'Unknown')
        }
        
        profile.raw_data.setdefault('onionscan', []).append(result)
        
    except:
        pass
