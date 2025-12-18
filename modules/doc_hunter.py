"""
Doc Hunter Module.
Combines logic from Metagoofil and FOCA.
Searches for public documents (PDF, DOCX, XLSX) and extracts metadata.
"""
from loguru import logger
from core.engine import Profile
import requests
from bs4 import BeautifulSoup
import os
import shutil
from urllib.parse import urljoin

# Metadata
META = {
    'name': 'doc_hunter',
    'description': 'Document Discovery & Metadata Analysis',
    'category': 'Recon',
    'risk': 'medium', 
    'emoji': '📄'
}

EXTENSIONS = ['pdf', 'docx', 'xlsx', 'pptx', 'txt']

def scan(target: str, profile: Profile):
    """
    Searches for documents on the target domain.
    """
    logger.info(f"[DocHunter] Hunting documents on {target}...")
    
    if not target.startswith('http'):
        target = 'https://' + target
        
    found_docs = []
    
    try:
        # 1. Naive crawl/scrape for links ending in extensions
        # Real Metagoofil uses Google Dorks (site:target.com filetype:pdf)
        # We will try a simple homepage scrape + Google Dork simulation if possible
        # (For now, homepage scrape for safety/compliance)
        
        res = requests.get(target, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            url = urljoin(target, href)
            
            if any(url.lower().endswith(ext) for ext in EXTENSIONS):
                logger.info(f"  └─ Found Document: {url}")
                found_docs.append(url)
                
        # 2. Add Google Dork suggestion to profile (since we can't always scrape Google directly without blockage)
        dorks = [f"site:{target} filetype:{ext}" for ext in EXTENSIONS]
        profile.add_metadata({'doc_dorks': dorks})
        
        # 3. Metadata Extraction (FOCA-lite)
        # If we found docs, try to download one and extract metadata
        if found_docs:
            from modules import exiftool
            
            # Temporary dir
            import tempfile
            temp_dir = tempfile.mkdtemp()
            
            count = 0
            for doc_url in found_docs:
                if count >= 3: break # Limit analysis
                
                try:
                    local_filename = doc_url.split('/')[-1]
                    local_path = os.path.join(temp_dir, local_filename)
                    
                    logger.info(f"[DocHunter] Downloading {local_filename} for analysis...")
                    with requests.get(doc_url, stream=True, timeout=10) as r:
                         with open(local_path, 'wb') as f:
                            shutil.copyfileobj(r.raw, f)
                            
                    # Run ExifTool
                    meta = exiftool.get_metadata(local_path)
                    if meta:
                        logger.success(f"[DocHunter] Metadata found in {local_filename}")
                        profile.add_metadata({'document_metadata': {
                            'url': doc_url,
                            'meta': meta
                        }})
                    
                    count += 1
                except Exception as e:
                    logger.warning(f"[DocHunter] Analysis failed for {doc_url}: {e}")
            
            shutil.rmtree(temp_dir)
            
        profile.add_metadata({'found_documents': found_docs})

    except Exception as e:
        logger.error(f"[DocHunter] Failed: {e}")
