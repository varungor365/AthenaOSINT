"""
Breach Harvester Module.
Autonomously searches for and downloads public database dumps and sensitive files.
Now enhanced with Google Dorking for deep discovery.
"""
import requests
import os
from loguru import logger
from pathlib import Path
from core.background_worker import UPLOAD_DIR
from config import get_config

# Metadata
META = {
    'name': 'breach_harvester',
    'description': 'Deep Web & Dork Harvester',
    'category': 'harvest',
    'risk': 'high', 
    'emoji': '📥'
}

def scan(target: str, profile):
    """
    Performs deep harvesting using Google Dorks and known index checks.
    """
    logger.info(f"[{META['name']}] Initiating deep harvest query: {target}")
    
    found_resources = []
    
    # 1. Google Dorking (The "Deep" Part)
    try:
        from googlesearch import search
        
        # Aggressive dorks for 16GB RAM power users
        dorks = [
            f"site:pastebin.com {target}",
            f"site:github.com {target} password",
            f"inurl:env {target}",
            f"filetype:sql {target}",
            f"filetype:log {target} password",
            f"index of / {target}" # Open Directory
        ]
        
        for dork in dorks:
            logger.info(f"[{META['name']}] Dorking: {dork}")
            # Max 10 results per dork to avoid ban, but deep enough
            results = search(dork, num_results=10)
            
            for url in results:
                profile.add_metadata({'type': 'exposed_resource', 'url': url, 'dork': dork})
                found_resources.append(url)
                
                # Check for direct file downloads (SQL, ENV, LOG)
                if url.endswith(('.sql', '.env', '.log', '.txt')):
                    _attempt_download(url, target)
                    
    except ImportError:
        logger.warning(f"[{META['name']}] googlesearch-python not installed. Skipping dorks.")
    except Exception as e:
        logger.error(f"[{META['name']}] Dorking failed: {e}")

    # 2. Local Simulation (Keep this for reliable demo/testing)
    if "test" in target or "demo" in target:
        dummy_dump_content = f"email,password,hash\nadmin@{target},123456,md5hash"
        dump_name = f"{target}_simulated_dump.csv"
        dump_path = UPLOAD_DIR / dump_name
        try:
            with open(dump_path, 'w') as f:
                f.write(dummy_dump_content)
            profile.add_metadata({'dump_acquired': dump_name})
        except:
            pass

    return found_resources

def _attempt_download(url: str, target: str):
    """Attempt to download a found resource."""
    try:
        filename = url.split('/')[-1]
        # Sanitize filename
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in ('-','_','.')]).rstrip()
        if not filename: filename = f"download_{os.urandom(4).hex()}.txt"
        
        save_path = UPLOAD_DIR / f"harvested_{filename}"
        
        # Stream download (good for RAM usage)
        with requests.get(url, stream=True, timeout=10) as r:
            r.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        logger.success(f"[{META['name']}] Downloaded: {filename}")
        
    except Exception as e:
        logger.warning(f"[{META['name']}] Failed to download {url}: {e}")
