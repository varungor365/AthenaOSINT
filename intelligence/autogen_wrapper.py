"""
AutoGen Integration for AthenaOSINT.
Defines a team of agents for complex investigation tasks.
"""
import os
from loguru import logger
import autogen
from config import get_config

class MultiAgentSystem:
    def __init__(self):
        self.config = get_config()
        self.api_key = self.config.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            logger.warning("AutoGen disabled: No OPENAI_API_KEY found.")
            self.enabled = False
            return
            
        self.enabled = True
        
        # Configuration for LLMs
        self.llm_config = {
            "config_list": [{"model": "gpt-4", "api_key": self.api_key}], # Defaults to GPT-4 if available, highly recommended for AutoGen
            "seed": 42,
            "temperature": 0
        }
        
    def run_investigation(self, objective: str):
        """Run a multi-agent investigation conversation."""
        if not self.enabled:
            return "Multi-Agent System is disabled (Missing API Key)."
            
        try:
            # 1. User Proxy (The Admin / Executor)
            # Acts as the bridge between user request and agents.
            # code_execution_config={"work_dir": "data/workspace"} allows agents to write/run code safely
            user_proxy = autogen.UserProxyAgent(
                name="Athena_Admin",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=5,
                is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
                code_execution_config={
                    "work_dir": "data/workspace",
                    "use_docker": False # Start with local for ease, warn user
                },
                system_message="I am the admin. I execute code and approve plans. Report final results to me."
            )
            
            # 2. Researcher Agent
            # Good at searching, planning, and synthesis
            researcher = autogen.AssistantAgent(
                name="OSINT_Researcher",
                llm_config=self.llm_config,
                system_message="""You are an expert OSINT Investigator. 
                Your goal is to solve the user's objective using available tools and python code.
                Plan your approach. If you need to fetch data, write python scripts to do so.
                When you have the final answer, append 'TERMINATE' to your message."""
            )
            
            # 3. Start Conversation
            logger.info(f"Starting AutoGen investigation: {objective}")
            
            user_proxy.initiate_chat(
                researcher,
                message=f"Investigation Objective: {objective}"
            )
            
            # Retrieve chat history
            # user_proxy.chat_messages[researcher] gives the history
            history = user_proxy.chat_messages[researcher]
            
            # Extract final summary or last meaningful message
            summary = "\n".join([f"[{m['role']}]: {m['content']}" for m in history])
            return summary
            
        except Exception as e:
            logger.error(f"AutoGen Error: {e}")
            return f"The Multi-Agent team encountered an error: {e}"
