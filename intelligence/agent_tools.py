"""
Agent Tool Wrapper.
Exposes AthenaOSINT modules as standardized tools for AutoGen agents.
"""
import importlib
from typing import Dict, Any, List, Optional
from loguru import logger
from core.engine import Profile
from modules.registry import MODULE_REGISTRY

class ToolRegistry:
    """
    Manages the registration and execution of OSINT tools for the AI agents.
    """
    
    def __init__(self):
        self.registry = MODULE_REGISTRY

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Returns a list of tool definitions formatted for AutoGen/LLM consumption.
        """
        tools = []
        for name, meta in self.registry.items():
            tools.append({
                "name": name,
                "description": meta.get('desc') or meta.get('description', 'No description'),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": f"The target {meta.get('type', 'value')} to scan."
                        }
                    },
                    "required": ["target"]
                }
            })
        return tools

    def execute_tool(self, tool_name: str, target: str) -> str:
        """
        Executes a specific OSINT tool and returns a summary of findings.
        
        Args:
            tool_name: Name of the module (e.g., 'shodan', 'sherlock')
            target: The query string (IP, email, username)
            
        Returns:
            String summary of the findings.
        """
        if tool_name not in self.registry:
            return f"Error: Tool '{tool_name}' not found."
            
        logger.info(f"Agent executing tool: {tool_name} on {target}")
        
        # 1. Setup Profile
        # We create a temporary profile just to capture this tool's output
        target_type = self.registry[tool_name].get('type', 'unknown')
        profile = Profile(target_query=target, target_type=target_type)
        
        # 2. Run Module
        try:
            module = importlib.import_module(f'modules.{tool_name}')
            
            if hasattr(module, 'scan'):
                module.scan(target, profile)
            else:
                return f"Error: Module '{tool_name}' has no scan() function."
                
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
            
        # 3. Summarize Results from Profile
        return self._summarize_profile(profile, tool_name)

    def _summarize_profile(self, profile: Profile, tool_name: str) -> str:
        """
        Convert the profile data into a concise text summary for the AI.
        """
        summary_parts = []
        
        # Key Findings
        if profile.emails:
            summary_parts.append(f"Found Emails: {', '.join(profile.emails)}")
        if profile.usernames:
            users = [f"{u} ({p})" for p, u in profile.usernames.items()]
            summary_parts.append(f"Found Usernames: {', '.join(users)}")
        if profile.phone_numbers:
            summary_parts.append(f"Found Phones: {', '.join(profile.phone_numbers)}")
        if profile.domains:
            summary_parts.append(f"Found Domains: {', '.join(profile.domains)}")
        if profile.subdomains:
             # Limit to 10
            subs = profile.subdomains[:10]
            summary_parts.append(f"Found Subdomains: {', '.join(subs)} ({len(profile.subdomains)} total)")
        if profile.related_ips:
            summary_parts.append(f"Found IPs: {', '.join(profile.related_ips)}")
            
        # Raw Data Inspection (Module specific)
        raw = profile.raw_data.get(f"{tool_name}_data") or profile.raw_data.get(tool_name)
        if raw:
            import json
            # Truncate if too long (max 500 chars)
            raw_str = json.dumps(raw, default=str)
            if len(raw_str) > 1000:
                raw_str = raw_str[:1000] + "... (truncated)"
            summary_parts.append(f"Raw Data Snippet: {raw_str}")
            
        # Errors
        if profile.errors:
            errs = [e['error'] for e in profile.errors]
            summary_parts.append(f"Errors Encountered: {', '.join(errs)}")
            
        if not summary_parts:
            return f"Tool '{tool_name}' completed but yielded no structured data."
            
        return "\n".join(summary_parts)
