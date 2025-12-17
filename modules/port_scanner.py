"""
Port Scanner Module.
Active reconnaissance to identify exposed services on an IP/Domain.
"""

import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, Style
from core.engine import Profile

META = {
    'description': 'Scans top 20 common ports to identify services',
    'target_type': 'ip, domain',
    'requirements': 'None'
}

# Top 20 Common Ports
COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 
    443, 445, 993, 995, 1433, 3306, 3389, 5900, 8000, 8080
]

PORT_NAMES = {
    21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
    80: 'HTTP', 443: 'HTTPS', 445: 'SMB', 3306: 'MySQL', 3389: 'RDP',
    8080: 'HTTP-Alt'
}

def check_port(target_ip: str, port: int) -> int:
    """Check a single port. Returns port if open, 0 if closed."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0) # 1 sec timeout
        result = sock.connect_ex((target_ip, port))
        sock.close()
        return port if result == 0 else 0
    except:
        return 0

def scan(target: str, profile: Profile) -> None:
    """Run Port Scanner."""
    print(f"{Fore.CYAN}[+] Running Active Port Scanner...{Style.RESET_ALL}")
    
    # Resolve IP if target is domain
    target_ip = target
    try:
        # Simple heuristic to identify domain vs IP
        if any(c.isalpha() for c in target):
            target_ip = socket.gethostbyname(target)
            print(f"  {Fore.BLUE}ℹ Resolved {target} -> {target_ip}{Style.RESET_ALL}")
    except Exception as e:
        print(f"  {Fore.RED}└─ Could not resolve target: {e}{Style.RESET_ALL}")
        return

    open_ports = []
    
    # Threaded Scan
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_port, target_ip, port): port for port in COMMON_PORTS}
        for future in futures:
            res = future.result()
            if res:
                open_ports.append(res)
                
    if open_ports:
        print(f"  {Fore.GREEN}└─ Open Ports Found:{Style.RESET_ALL}")
        results = []
        for p in sorted(open_ports):
            service = PORT_NAMES.get(p, 'Unknown')
            print(f"     - {p}/tcp ({service})")
            results.append({'port': p, 'service': service})
            
        # Store in profile
        profile.raw_data.setdefault('open_ports', []).extend(results)
    else:
        print(f"  {Fore.YELLOW}└─ No common ports found open (filtered/closed).{Style.RESET_ALL}")
