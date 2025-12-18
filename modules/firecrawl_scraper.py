"""
Firecrawl Scraper Module.
Uses Firecrawl SDK to turn websites into LLM-ready markdown.
requires FIRECRAWL_API_KEY in .env
"""
from loguru import logger
from config import get_config
from core.engine import Profile

# Metadata
META = {
    'name': 'firecrawl',
    'description': 'Turn websites into LLM-ready markdown (Firecrawl)',
    'category': 'scraper',
    'risk': 'medium', 
    'emoji': '🔥'
}

def scan(target: str, profile: Profile):
    """
    Scrapes the target URL using Firecrawl app.
    """
    if not target.startswith('http'):
        logger.info("[Firecrawl] Target must be a URL.")
        return

    config = get_config()
    api_key = config.get('FIRECRAWL_API_KEY')
    
    if not api_key:
        logger.error("[Firecrawl] Missing FIRECRAWL_API_KEY.")
        profile.add_error('firecrawl', 'Missing API Key')
        return

    try:
        from firecrawl import FirecrawlApp
        app = FirecrawlApp(api_key=api_key)
        
        logger.info(f"[Firecrawl] Scraping {target}...")
        
        # Scrape URL
        scrape_result = app.scrape_url(target, params={'formats': ['markdown']})
        
        if scrape_result and 'markdown' in scrape_result:
            markdown = scrape_result['markdown']
            
            # Store full content (maybe too large for metadata, better handling via file?)
            # For now, store snippet and save full to a file/memory bank
            snippet = markdown[:500] + "..."
            profile.add_metadata({'firecrawl_snippet': snippet})
            
            # TODO: Integrate with IntelligenceStore directly?
            # For now, just logging success
            logger.success(f"[Firecrawl] Successfully scraped {len(markdown)} chars.")
            
    except Exception as e:
        logger.error(f"[Firecrawl] Failed: {e}")
        profile.add_error('firecrawl', str(e))
