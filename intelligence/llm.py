"""
LLM Client for AthenaOSINT.

This module provides a unified interface for AI operations, supporting
both cloud (Groq) and local (Ollama) providers with automatic fallback.
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from loguru import logger

from config import get_config
from core.api_manager import get_api_manager


class LLMClient:
    """Unified client for AI operations."""
    
    def __init__(self):
        """Initialize the LLM client."""
        self.config = get_config()
        self.api_manager = get_api_manager()
        
        # Auto-detect optimal provider
        configured_provider = self.config.get('AI_PROVIDER', 'groq')
        
        groq_key = self.api_manager.get_key('GROQ')
        openai_key = self.api_manager.get_key('OPENAI')
        openrouter_key = self.config.get('OPENROUTER_API_KEY')
        
        if openrouter_key:
             logger.info("OpenRouter key found. Using OpenRouter as primary provider.")
             self.provider = 'openrouter'
        elif configured_provider == 'groq' and not groq_key:
            logger.info("No Groq API key found. Falling back to Local AI (Ollama).")
            self.provider = 'ollama'
        elif configured_provider == 'openai' and not openai_key:
             logger.info("No OpenAI API key found. Falling back to Local AI (Ollama).")
             self.provider = 'ollama'
        else:
            self.provider = configured_provider

        self.ollama_host = self.config.get('OLLAMA_HOST', 'http://localhost:11434')
        self.ollama_model = self.config.get('OLLAMA_MODEL', 'llama3:8b')
        
    def generate_text(self, prompt: str, system_prompt: str = None) -> str:
        """Generate text from the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system context
            
        Returns:
            Generated text response
        """
        if self.provider == 'groq':
            try:
                return self._query_groq(prompt, system_prompt)
            except Exception as e:
                logger.error(f"Groq generation failed: {e}. Falling back to Ollama.")
                return self._query_ollama(prompt, system_prompt)
        
        elif self.provider == 'openrouter':
            try:
                return self._query_openrouter(prompt, system_prompt)
            except Exception as e:
                logger.error(f"OpenRouter generation failed: {e}. Falling back to Ollama.")
                return self._query_ollama(prompt, system_prompt)
                
        elif self.provider == 'ollama':
            return self._query_ollama(prompt, system_prompt)
            
        else:
            logger.error(f"Unknown AI provider: {self.provider}")
            return "AI Error: Unknown provider"

    def _query_groq(self, prompt: str, system_prompt: str = None) -> str:
        """Query Groq API."""
        api_key = self.api_manager.get_key('GROQ')
        if not api_key:
            raise ValueError("No Groq API keys available")
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "messages": messages,
            "model": "llama3-70b-8192", # Use larger model on cloud
            "temperature": 0.5,
            "max_tokens": 1024
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            self.api_manager.report_error('GROQ', api_key, response.status_code)
            raise Exception(f"Groq API Error: {response.status_code} - {response.text}")

    def _query_openrouter(self, prompt: str, system_prompt: str = None) -> str:
        """Query OpenRouter API."""
        api_key = self.config.get('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("No OpenRouter API key available")
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://athenaosint.com", # Required by OpenRouter
            "X-Title": "AthenaOSINT",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "openai/gpt-3.5-turbo", # Default low cost model
            "messages": messages,
            "max_tokens": 1024
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"OpenRouter Error: {response.status_code} - {response.text}")

    def _query_ollama(self, prompt: str, system_prompt: str = None) -> str:
        """Query local Ollama instance."""
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False
        }
        if system_prompt:
             payload["system"] = system_prompt
             
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json=payload,
                timeout=60 # Local models can be slow
            )
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                raise Exception(f"Ollama Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to Ollama. Is it running?")

    def analyze_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a profile and generate insights.
        
        Args:
            profile_data: Dictionary representation of a Profile
            
        Returns:
            Dictionary containing insights and suggested actions
        """
        system_prompt = """You are a senior OSINT investigator. Analyze the provided target data.
        Identify patterns, inconsistencies, and high-value leads.
        Output MUST be valid JSON with keys: 'summary', 'risk_score' (1-10), 'key_findings' (list), 'suggested_actions' (list).
        """
        
        # Summarize data to fit context window
        summary_data = {
            "target": profile_data.get('target_query'),
            "emails": profile_data.get('emails', [])[:10],
            "usernames": list(profile_data.get('usernames', {}).values())[:10],
            "domains": profile_data.get('domains', [])[:10],
            "breach_count": len(profile_data.get('breaches', [])),
        }
        
        prompt = f"Analyze this OSINT profile: {json.dumps(summary_data, indent=2)}"
        
        response_text = self.generate_text(prompt, system_prompt)
        
        # Clean response to ensure JSON
        try:
            # Find first { and last }
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                return {"error": "Failed to parse AI response", "raw": response_text}
        except Exception as e:
            return {"error": f"JSON parse error: {e}", "raw": response_text}
