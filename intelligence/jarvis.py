"""
Project JARVIS - The Intelligence Agent for AthenaOSINT.

This module provides the "Brain" of the system, capable of:
1. Conversational Chat (Hinglish/English).
2. Command Execution (Triggering Scans).
3. Code Generation (Writing new modules/scripts).
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger

from intelligence.llm import LLMClient
from core.engine import AthenaEngine
from config import get_config

CONFIG = get_config()

class JarvisAgent:
    """The AI Agent that controls AthenaOSINT."""
    
    def __init__(self):
        self.llm = LLMClient()
        self.history: List[Dict[str, str]] = []
        self.system_prompt = """
You are JARVIS, the AI assistant for AthenaOSINT.
Your persona: Efficient, slightly witty, highly competent cyber-intelligence AI.
You speak: English, Hindi, or "Hinglish" depending on the user.

You have access to the following TOOLS:
1. SCAN: search for information on a target (email, username, domain).
2. CODE: write Python code or scripts to solve a problem.
3. EXPLAIN: explain vulnerability or OSINT concept.
4. CHAT: general conversation.

INSTRUCTIONS:
- If the user asks to "scan" or "check" or "find info" on a target, respond with valid JSON: {"tool": "SCAN", "target": "...", "modules": ["list", "of", "modules"]}
- If the user asks to "write code", "create a script", or "make a module", respond with valid JSON: {"tool": "CODE", "filename": "suggested_name.py", "prompt": "refined coding prompt"}
- Otherwise, respond with normal text for CHAT.

Do not allow dangerous system commands outside of the defined scopes.
"""

    def process_input(self, user_text: str) -> Dict[str, Any]:
        """Process user input and determine action."""
        
        # 1. Check for basic intent via Regex (Faster than LLM for simple stuff)
        scan_match = re.search(r'(scan|check|investigate|target)\s+([a-zA-Z0-9._@-]+)', user_text, re.IGNORECASE)
        
        # 2. If simple scan, return immediately
        if scan_match and len(user_text.split()) < 10:
             target = scan_match.group(2)
             return {
                 "type": "action",
                 "action": "scan",
                 "target": target,
                 "response": f"Affirmative. Initiating scan protocols for {target}."
             }

        # 3. For complex requests, consult LLM
        response_text = self.llm.generate_text(
            prompt=f"User said: '{user_text}'. Analyze intent and respond as per system instructions.",
            system_prompt=self.system_prompt,
            max_tokens=500
        )
        
        # Try to parse JSON from LLM
        try:
            # Extract JSON if embedded in text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                
                if data.get('tool') == 'SCAN':
                    return {
                        "type": "action",
                        "action": "scan",
                        "target": data.get('target'),
                        "response": f"Running detailed scan on {data.get('target')}."
                    }
                    
                if data.get('tool') == 'CODE':
                    return self._generate_code_action(data.get('filename'), data.get('prompt'))
                    
        except Exception:
            pass # Fallback to chat
            
        return {
            "type": "chat",
            "response": response_text
        }

    def _generate_code_action(self, filename: str, prompt: str) -> Dict[str, Any]:
        """Handle code generation request."""
        
        code_system_prompt = "You are an expert Python Security Developer. Write clean, working Python code. Output ONLY the code block."
        
        code = self.llm.generate_text(
            prompt=f"Write a Python script for: {prompt}",
            system_prompt=code_system_prompt,
            max_tokens=2000
        )
        
        # Strip markdown
        code = code.replace("```python", "").replace("```", "").strip()
        
        # Save to 'generated' folder
        output_dir = Path("generated")
        output_dir.mkdir(exist_ok=True)
        
        file_path = output_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
            
        return {
            "type": "action",
            "action": "code",
            "filename": str(file_path),
            "response": f"I have written the code for you. Saved to {file_path}. Would you like me to explain it?"
        }

