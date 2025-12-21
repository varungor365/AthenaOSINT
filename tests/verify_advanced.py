
import os
import sys
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine import Profile

def verify_modules():
    print("[-] Verifying Advanced Recon Modules...")
    
    # Mock Profile
    profile = Profile(target_query="example.com", target_type="domain")
    
    modules_to_test = ['redghost', 'passive_recon', 'go_recon', 'spiderfoot', 'websift', 'bbot', 'ghost_track', 'danxy']
    
    for mod_name in modules_to_test:
        print(f"[*] Testing import of {mod_name}...")
        try:
            mod = __import__(f"modules.{mod_name}", fromlist=['scan'])
            if hasattr(mod, 'scan'):
                print(f"  [+] {mod_name} loaded successfully.")
            else:
                print(f"  [X] {mod_name} missing scan() function.")
                
            # Dry run check (we don't want to actually install big tools during quick verify if possible, or we check if install function exists)
            if hasattr(mod, 'install'):
                print(f"  [+] {mod_name} has install routine.")
                
            # For go_recon, check if checks for go
            if mod_name == 'go_recon':
                if shutil.which('go'):
                     print("  [+] Go seems to be installed.")
                else:
                     print("  [!] Go is NOT installed. go_recon will fail at runtime.")
                     
        except ImportError as e:
            print(f"  [X] Failed to import {mod_name}: {e}")

    print("[-] Verification Complete.")

if __name__ == "__main__":
    verify_modules()
