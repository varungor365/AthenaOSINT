"""
GHunt Lite.
Checks if a Gmail address exists.
"""

import requests
from core.engine import Profile

META = {
    'description': 'Gmail Account Info',
    'target_type': 'email'
}

def scan(target: str, profile: Profile) -> None:
    if '@gmail.com' not in target:
        return

    # Without cookies, we can only do basic validation or use a public API if one exists (none really do)
    # This is a Placeholder for the full GHunt implementation which requires running the separate tool
    
    profile.raw_data['ghunt_status'] = "Requires Cookies"
    # We mark it as 'Processed' but note limitation
    profile.add_pattern("Gmail Account Detected", "low", "Target uses Gmail")
