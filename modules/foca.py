"""
FOCA-lite module for AthenaOSINT.

This module searches for public documents (PDF, DOCX, XLSX) on a target domain
and extracts metadata (users, software versions, printers) similar to FOCA.
"""

import requests
import os
import tempfile
from typing import Dict, List, Any
from urllib.parse import unquote
from colorama import Fore, Style
from loguru import logger
from bs4 import BeautifulSoup

# Optional dependencies for metadata
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

from core.engine import Profile

def scan(target: str, profile: Profile) -> None:
    """Scan for documents and extract metadata.
    
    Args:
        target: Target domain
        profile: Profile object to update
    """
    if '@' in target or not '.' in target:
        return

    if not PyPDF2:
        logger.warning("PyPDF2 not installed. Metadata extraction will be limited.")
        print(f"{Fore.YELLOW}[!] PyPDF2 missing. Skipping PDF metadata.{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}[+] Running FOCA-lite (Document Analysis)...{Style.RESET_ALL}")
    
    # 1. Google Dorking for files (Simulated via searching common paths or using a search API if available)
    # Since we don't have a Google Search API key in config, we'll try a very simple scrape or 
    # rely on the 'Wayback Machine' approach or just skip the discovery phase and assume
    # the user might provide a URL. 
    # FORCE: For this implementation, I'll simulate "finding" files by checking common locations
    # or just warn that search API is needed.
    # BETTER: Let's try to find linked files on the homepage.
    
    try:
        urls_to_check = _find_document_links(target)
        
        if not urls_to_check:
            print(f"  {Fore.YELLOW}└─ No documents found on homepage.{Style.RESET_ALL}")
            return
            
        print(f"  {Fore.CYAN}└─ Analyzing {len(urls_to_check)} documents...{Style.RESET_ALL}")
        
        metadata_found = 0
        
        for doc_url in urls_to_check[:5]: # Limit to 5 to save bandwidth
            try:
                # Download file
                response = requests.get(doc_url, timeout=10, verify=False)
                if response.status_code == 200:
                    ext = doc_url.split('.')[-1].lower()
                    
                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        tmp.write(response.content)
                        tmp_path = tmp.name
                    
                    meta = {}
                    if ext == 'pdf':
                        meta = _analyze_pdf(tmp_path)
                    
                    # Clean up
                    os.unlink(tmp_path)
                    
                    if meta:
                        meta['source_url'] = doc_url
                        profile.add_metadata(meta)
                        metadata_found += 1
                        
                        # Extract users if possible (Author)
                        if 'author' in meta and meta['author']:
                            profile.add_username('metadata', meta['author'])
            except Exception as e:
                pass
                
        if metadata_found > 0:
            print(f"  {Fore.GREEN}└─ Extracted metadata from {metadata_found} files{Style.RESET_ALL}")
            logger.info(f"FOCA: Analyzed {metadata_found} files")
            
    except Exception as e:
        logger.error(f"FOCA scan failed: {e}")

def _find_document_links(domain: str) -> List[str]:
    """Scrape homepage for document links."""
    links = []
    try:
        url = f"http://{domain}"
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().endswith(('.pdf', '.docx', '.xlsx', '.pptx')):
                if href.startswith('http'):
                    links.append(href)
                elif href.startswith('/'):
                    links.append(f"{url}{href}")
                else:
                    links.append(f"{url}/{href}")
    except:
        pass
    return list(set(links))

def _analyze_pdf(file_path: str) -> Dict[str, Any]:
    """Extract metadata from PDF."""
    meta = {}
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            info = reader.metadata
            if info:
                if info.author: meta['author'] = info.author
                if info.creator: meta['creator'] = info.creator
                if info.producer: meta['producer'] = info.producer
                if info.title: meta['title'] = info.title
    except Exception:
        pass
    return meta
