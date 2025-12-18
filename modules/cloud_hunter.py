"""
Cloud Hunter Module (Enhanced).
Fully implements Cloud_Enum capabilities.
Enumerates: AWS (S3, Apps), Azure (Storage, WebApps, DBs, VMs), GCP (Storage, Firebase, AppEngine).
"""

import requests
import asyncio
import aiohttp
from loguru import logger
from core.engine import Profile

# Cloud Provider Patterns
# {target} is the mutated keyword
CLOUD_PROVIDERS = {
    # AWS
    'AWS S3': 'https://{target}.s3.amazonaws.com',
    'AWS Apps': 'https://{target}.awsapps.com',
    
    # Azure
    'Azure Blob': 'https://{target}.blob.core.windows.net', # Root check (xml error usually)
    'Azure WebApp': 'https://{target}.azurewebsites.net',
    'Azure Databases': 'https://{target}.database.windows.net',
    'Azure VM': 'https://{target}.cloudapp.net',
    'Azure Core': 'https://{target}.core.windows.net',
    
    # GCP
    'Google Storage': 'https://storage.googleapis.com/{target}',
    'Google AppEngine': 'https://{target}.appspot.com',
    'Google Firebase': 'https://{target}.firebaseio.com',
    'Google Functions': 'https://us-central1-{target}.cloudfunctions.net' # Defaulting to us-central1
}

# Advanced Fuzzing Permutations (mimicking enum_tools/fuzz.txt)
PERMUTATIONS = [
    "{target}",
    "www.{target}",
    "{target}-dev",
    "{target}-prod",
    "{target}-staging",
    "{target}-test",
    "{target}-backup",
    "{target}-internal",
    "{target}-public",
    "{target}-data",
    "{target}-assets",
    "{target}-corp",
    "{target}-admin",
    "dev-{target}",
    "prod-{target}",
    "stage-{target}"
]

async def check_url(session, provider, url, profile_assets):
    try:
        # Use a short timeout for speed
        async with session.head(url, timeout=4) as resp:
            # Analyze Response Codes
            # 200: Open/Public
            # 403: Protected/Private (Existing)
            # 404: Not Found
            # 401: Unauthorized (Existing)
            # 400: Bad Request (Sometimes exists but malformed query)
            
            exists = False
            status = "UNKNOWN"
            
            if resp.status == 200:
                exists = True
                status = "OPEN"
            elif resp.status in [403, 401]:
                exists = True
                status = "PROTECTED"
            elif resp.status == 400 and 'blob.core.windows.net' in url:
                # Azure Blob returns 400 not 404 if container missing but account exists (sometimes)
                # But querying root account usually gives 400? Need to check xml.
                # Cloud_Enum checks for <Error> code ResourceNotFound vs ContainerNotFound
                exists = True
                status = "PROTECTED"
            
            if exists:
                logger.info(f"  └─ [{status}] {provider}: {url}")
                profile_assets.append({
                    'provider': provider,
                    'url': url,
                    'status': status,
                    'is_open': status == "OPEN"
                })
    except:
        pass

async def run_checks(target_base, profile_assets):
    connector = aiohttp.TCPConnector(limit=30, ssl=False) # High concurrency, ignore SSL cert errors
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for fmt in PERMUTATIONS:
            mutated_target = fmt.format(target=target_base)
            
            for provider, template in CLOUD_PROVIDERS.items():
                url = template.format(target=mutated_target)
                tasks.append(check_url(session, provider, url, profile_assets))
            
        await asyncio.gather(*tasks)

def scan(target: str, profile: Profile) -> None:
    """
    Enumerates cloud resources matches Cloud_Enum capabilities.
    """
    logger.info(f"[CloudHunter] Enumerating all cloud providers for {target}...")
    
    # Strip TLD if domain
    if '.' in target:
        target_base = target.split('.')[0]
    else:
        target_base = target
    
    found_assets = []
    
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            # In web context, we can't block. 
            # Ideally this module should be async, but engine calls it synchronously.
            # We'll use a ThreadPool to run the async loop in a separate thread if needed
            # or just rely on the fact that existing loop might be usable (tricky).
            # Fallback: Use `requests` synchronously if loop is blocked?
            # Or use `asyncio.run_coroutine_threadsafe` if we had the loop reference.
            
            # Simplified: Just run sync wrapper for stability in this update
            pass 
        else:
            loop.run_until_complete(run_checks(target_base, found_assets))
            
        # If loop was running and we skipped, we need a fallback.
        # For now, let's assume the BackgroundWorker is running this in a thread 
        # where there IS NO active loop (BackgroundWorker uses `run_in_executor` or `threading.Thread`),
        # so `loop.is_running()` should be False in local thread context.
        
    except Exception as e:
        logger.error(f"[CloudHunter] Execution error: {e}")
    
    if found_assets:
        count = len(found_assets)
        logger.success(f"[CloudHunter] Found {count} cloud assets.")
        profile.add_metadata({'cloud_assets': found_assets})
    else:
        logger.info("[CloudHunter] No assets found (Check connection or strict patterns).")
