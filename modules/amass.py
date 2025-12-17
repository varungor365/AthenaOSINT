"""
Amass Wrapper.
Wraps the Amass binary for subdomain enumeration.
"""

import shutil
import subprocess
from core.engine import Profile

META = {
    'description': 'OWASP Amass Subdomain Enum',
    'target_type': 'domain'
}

def scan(target: str, profile: Profile) -> None:
    if not shutil.which('amass'):
        print("[-] Amass not installed")
        return

    try:
        # Run amass enum -d target -passive
        cmd = ['amass', 'enum', '-d', target, '-passive', '-nocolor']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        subdomains = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        
        if subdomains:
            profile.raw_data.setdefault('subdomains', []).extend(subdomains)
            profile.add_pattern(f"Amass: {len(subdomains)} subs", "low", "Amass enumeration")
            
    except Exception as e:
        print(f"Amass error: {e}")
