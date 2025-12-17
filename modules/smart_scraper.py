"""
Smart Scraper Module using ScrapeGraphAI.
Extracts structured intelligence from unstructured webpages using LLMs.
"""
import os
from loguru import logger
from config import get_config

# Metadata for Auto-Discovery
META = {
    'name': 'smart_scraper',
    'description': 'AI-Powered Deep Web Scraper',
    'category': 'scraper', # execution order: late
    'risk': 'medium', # makes requests
    'emoji': '🕷️'
}

def scan(target: str, profile):
    """
    Run ScrapeGraphAI on the target URL (if target is a URL).
    """
    if not (target.startswith('http://') or target.startswith('https://')):
        logger.info("[SmartScraper] Target is not a URL, skipping.")
        return

    config = get_config()
    api_key = config.get('OPENAI_API_KEY')
    
    if not api_key:
        logger.error("[SmartScraper] No OPENAI_API_KEY found.")
        profile.add_error('smart_scraper', 'Missing OpenAI API Key')
        return

    try:
        from scrapegraphai.graphs import SmartScraperGraph

        graph_config = {
            "llm": {
                "api_key": api_key,
                "model": "openai/gpt-3.5-turbo",
            },
            "verbose": True,
            "headless": True
        }

        # Define extraction schema
        prompt = "Extract all email addresses, phone numbers, physical addresses, and social media links found on this page. Return as a JSON."

        smart_scraper_graph = SmartScraperGraph(
            prompt=prompt,
            source=target,
            config=graph_config
        )

        result = smart_scraper_graph.run()
        
        if result:
            logger.info(f"[SmartScraper] Extracted Data: {result}")
            
            # Process Emails
            if 'emails' in result and isinstance(result['emails'], list):
                for email in result['emails']:
                    profile.add_email(email)
            
            # Process Phones
            if 'phone_numbers' in result and isinstance(result['phone_numbers'], list):
                for phone in result['phone_numbers']:
                    profile.add_phone(phone)
                    
            # Store full result
            profile.add_metadata({'source': 'smart_scraper', 'data': result})
            
    except Exception as e:
        logger.error(f"[SmartScraper] Failed: {e}")
        profile.add_error('smart_scraper', str(e))
