"""
Shodan Module.
Process IP addresses to find open ports and banners.
"""

import requests
from core.engine import Profile
from config import get_config

META = {
    'description': 'IoT Search Engine',
    'target_type': 'ip'
}

def scan(target: str, profile: Profile) -> None:
    api_key = get_config().get('SHODAN_API_KEY')
    if not api_key:
        print("[-] Shodan API Key missing")
        return

    try:
        url = f"https://api.shodan.io/shodan/host/{target}?key={api_key}"
        res = requests.get(url, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            
            summary = {
                'os': data.get('os'),
                'ports': data.get('ports', []),
                'hostnames': data.get('hostnames', []),
                'org': data.get('org'),
                'city': data.get('city'),
                'country': data.get('country_name')
            }
            
            profile.raw_data['shodan_data'] = summary
            profile.locations.append(f"{summary['city']}, {summary['country']}")
            
            for p in summary['ports']:
                profile.add_pattern(f"Open Port: {p}", "medium", f"Shodan detected port {p}")
                
    except Exception as e:
        print(f"Shodan error: {e}")
