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
    
    # 1. Official Shodan API
    if api_key:
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
                return # Done
                
        except Exception as e:
            print(f"Shodan API error: {e}")

    # 2. Fallback: Local Port Scan (Socket)
    print(f"[-] Shodan API skipped. Running local port scan on {target}...")
    import socket
    
    common_ports = [21, 22, 23, 25, 53, 80, 443, 8080, 3306, 3389]
    open_ports = []
    
    for port in common_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((target, port))
        if result == 0:
            open_ports.append(port)
            print(f"  [+] Open Port: {port}")
        sock.close()
        
    if open_ports:
        profile.raw_data['shodan_data'] = {'ports': open_ports, 'source': 'local_scan'}
        for p in open_ports:
            profile.add_pattern(f"Open Port: {p}", "medium", f"Local scan detected port {p}")
