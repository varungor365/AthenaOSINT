"""
GhostTrack Module.
IP and Phone Number geolocation and carrier tracking.
Inspired by 'GhostTrack' tool.
"""
import requests
from loguru import logger
from core.engine import Profile

# Metadata
META = {
    'name': 'ghost_track',
    'description': 'IP & Phone Geolocation Tracker',
    'category': 'Real World',
    'risk': 'safe',
    'emoji': '👻'
}

def scan(target: str, profile: Profile):
    """
    Identifies if target is IP or Phone and runs tracking.
    """
    import re
    
    # 1. IP Tracking
    # Simple regex for IPv4
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", target):
        logger.info(f"[GhostTrack] Tracking IP: {target}")
        try:
            # Using ip-api (free tier, no key needed)
            res = requests.get(f"http://ip-api.com/json/{target}", timeout=10)
            data = res.json()
            
            if data['status'] == 'success':
                profile.add_metadata({
                    'type': 'ip_location',
                    'country': data.get('country'),
                    'city': data.get('city'),
                    'isp': data.get('isp'),
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'org': data.get('org')
                })
                logger.success(f"[GhostTrack] Located IP in {data.get('city')}, {data.get('country')}")
            else:
                logger.warning(f"[GhostTrack] IP-API returned fail.")
        except Exception as e:
            logger.error(f"[GhostTrack] IP Track failed: {e}")

    # 2. Phone Tracking (Numverify/Mock)
    # Using libphonenumber logic via 'phoneinfoga' usually, but here is a lightweight lookup
    elif target.startswith('+') or target.isdigit():
        logger.info(f"[GhostTrack] Tracking Phone: {target}")
        # Note: robust phone tracking requires paid APIs (NumVerify, Twilio) or scraping.
        # We will infer basic country code here as a fallback if no other tool picked it up.
        # (This is a simplified implementation of what GhostTrack does)
        pass 
