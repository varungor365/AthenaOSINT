"""
Breach Analyzer Module
---------------------
Uses AI to analyze processed breach data (combo lists) to identify high-value targets,
patterns, and risk assessments.
"""

import json
from typing import List, Dict, Any
from loguru import logger
from intelligence.llm import LLMClient

class BreachAnalyzer:
    """Analyzer for breach data using AI."""
    
    def __init__(self):
        self.llm = LLMClient()
        self.common_domains = {'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com'}
        
    def analyze_batch(self, combos: List[str]) -> Dict[str, Any]:
        """
        Analyze a batch of user:pass combos.
        Returns a dictionary with 'high_risk_targets', 'patterns', 'summary'.
        """
        # Filter for interesting potential targets first to save tokens
        interesting_candidates = []
        for combo in combos:
            try:
                user, _ = combo.split(':', 1)
                if '@' in user:
                    domain = user.split('@')[-1].lower()
                    if domain not in self.common_domains:
                        interesting_candidates.append(combo)
            except ValueError:
                continue
                
        if not interesting_candidates:
            return {
                "high_risk_targets": [],
                "patterns": "No corporate/interesting domains found.",
                "risk_level": "Low"
            }
            
        # Limit batch size for LLM
        analysis_batch = interesting_candidates[:50] 
        
        prompt = f"""
        Analyze the following list of breached credentials (User:Pass).
        Identify HIGH RISK targets (Government, Military, Large Corp, Infrastructure).
        Analyze password patterns (Reuse, Complexity).
        
        Credentials:
        {json.dumps(analysis_batch, indent=2)}
        
        Return JSON with:
        - "high_risk_targets": List of objects {{ "email": "...", "reason": "..." }}
        - "patterns": String summary of password patterns.
        - "risk_assessment": "Low", "Medium", "High"
        """
        
        system_prompt = "You are a Cyber Threat Intelligence Analyst. Focus on indentifying high-value targets in breach data."
        
        try:
            response = self.llm.generate_text(prompt, system_prompt)
            
            # Parse JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(response[start:end])
            else:
                return {"error": "Failed to parse AI response", "raw": response}
                
        except Exception as e:
            logger.error(f"AI Analysis failed: {e}")
            return {"error": str(e)}

