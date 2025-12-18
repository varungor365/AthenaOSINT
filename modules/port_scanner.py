"""
Port Scanner Module.
Active infrastructure mapping (Top 20 Ports).
"""
import socket
import concurrent.futures
from loguru import logger
from core.engine import Profile

# Metadata
META = {
    'name': 'port_scanner',
    'description': 'Basic Port Scanner (Active)',
    'category': 'Network',
    'risk': 'medium', # Active scanning
    'emoji': '🔌'
}

TOP_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080
]

def check_port(target, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            result = s.connect_ex((target, port))
            if result == 0:
                return port
    except:
        pass
    return None

def scan(target: str, profile: Profile):
    """
    Scans top ports on the target.
    """
    # IP or Domain?
    if 'http' in target:
        import urllib.parse
        target = urllib.parse.urlparse(target).netloc

    logger.info(f"[PortScanner] Scanning top {len(TOP_PORTS)} ports on {target}...")

    open_ports = []
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_port = {executor.submit(check_port, target, p): p for p in TOP_PORTS}
            for future in concurrent.futures.as_completed(future_to_port):
                port = future.result()
                if port:
                    open_ports.append(port)
                    logger.info(f"  └─ Port {port} OPEN")
                    
        profile.add_metadata({'open_ports': open_ports})
        logger.success(f"[PortScanner] Found {len(open_ports)} open ports.")
        
    except Exception as e:
        logger.error(f"[PortScanner] Scan failed: {e}")
        profile.add_error('port_scanner', str(e))
