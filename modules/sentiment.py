"""
Sentiment Analysis module for AthenaOSINT.

This module uses the AI layer to analyze the sentiment of gathered text
(bios, posts, metadata) to gauge the target's mood or intent.
"""

from colorama import Fore, Style
from loguru import logger
from typing import Dict, Any

from core.engine import Profile
from intelligence.llm import LLMClient

def scan(target: str, profile: Profile) -> None:
    """Analyze sentiment of gathered text.
    
    Args:
        target: Target identifier
        profile: Profile with gathered data
    """
    # This runs late in the pipeline, analyzing existing data
    
    # Gather text to analyze
    text_corpus = []
    
    # 1. Bios
    if 'social_details' in profile.raw_data:
        for site, details in profile.raw_data['social_details'].items():
            if details and details.get('bio'):
                text_corpus.append(f"Bio ({site}): {details['bio']}")
                
    # 2. Metadata (Author names, Titles)
    for meta in profile.metadata:
        if meta.get('title'):
            text_corpus.append(f"Document Title: {meta['title']}")
            
    if not text_corpus:
        logger.debug("Sentiment: No text to analyze")
        return

    print(f"{Fore.CYAN}[+] Running AI Sentiment Analysis...{Style.RESET_ALL}")
    
    try:
        llm = LLMClient()
        
        # Prepare prompt
        combined_text = "\n".join(text_corpus)
        prompt = f"""
        Analyze the sentiment and psychological profile of the person who wrote the following texts:
        {combined_text[:2000]}
        
        Return a concise JSON with:
        - "dominant_mood": (Positive, Negative, Neutral, Aggressive, Professional, etc.)
        - "risk_level": (Low, Medium, High)
        - "profiling_notes": One sentence summary.
        """
        
        # Since our LLM client returns text, we parse it or ask for plain text summary if easier
        # Let's ask for plain text for simplicity of display in this iteration
        
        analysis = llm.generate_text(prompt)
        
        # Store results
        profile.raw_data['sentiment_analysis'] = {
            'analysis_text': analysis,
            'source_count': len(text_corpus)
        }
        
        print(f"  {Fore.GREEN}└─ Sentiment Analysis Complete{Style.RESET_ALL}")
        
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        print(f"{Fore.RED}[!] Sentiment analysis failed: {e}{Style.RESET_ALL}")
