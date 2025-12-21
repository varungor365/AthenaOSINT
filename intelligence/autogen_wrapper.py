"""
AutoGen Integration for AthenaOSINT.
Defines a team of agents for complex investigation tasks using GroupChat.
"""
import os
import json
from loguru import logger
import autogen
from config import get_config
from intelligence.agent_tools import ToolRegistry

class MultiAgentSystem:
    def __init__(self):
        self.config = get_config()
        self.api_key = self.config.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            logger.warning("AutoGen disabled: No OPENAI_API_KEY found.")
            self.enabled = False
            return
            
        self.enabled = True
        self.tool_registry = ToolRegistry()
        
        # Configuration for LLMs
        self.llm_config = {
            "config_list": [{"model": "gpt-4", "api_key": self.api_key}],
            "seed": 42,
            "temperature": 0.1,
            # Tools will be injected dynamically or handled via function mapping
        }

    def run_investigation(self, objective: str, update_callback=None):
        """Run a multi-agent investigation conversation."""
        if not self.enabled:
            return "Multi-Agent System is disabled (Missing API Key)."
            
        try:
            # --- 1. Define Tools ---
            # We expose a generic 'run_osint_tool' function to the agents
            def run_osint_tool(tool_name: str, target: str) -> str:
                return self.tool_registry.execute_tool(tool_name, target)

            # Define the function signature for the LLM
            tools_config = {
                "functions": [
                    {
                        "name": "run_osint_tool",
                        "description": "Execute an OSINT tool to gather information.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "tool_name": {
                                    "type": "string", 
                                    "description": "Name of the tool (e.g., 'sherlock', 'shodan')."
                                },
                                "target": {
                                    "type": "string",
                                    "description": "The target to scan (email, IP, domain, username)."
                                }
                            },
                            "required": ["tool_name", "target"]
                        }
                    }
                ]
            }
            
            # Merge tools into llm_config
            agent_llm_config = self.llm_config.copy()
            agent_llm_config.update(tools_config)

            # --- 2. Define Agents ---
            
            # ADMIN: Executes the tools (UserProxyAgent)
            user_proxy = autogen.UserProxyAgent(
                name="Commander_Admin",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=10,
                is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
                code_execution_config={"work_dir": "data/workspace", "use_docker": False},
                function_map={"run_osint_tool": run_osint_tool},
                system_message="I execute tool calls. I do NOT plan. I report output back."
            )
            
            # RESEARCHER: High-level Planner
            leader = autogen.AssistantAgent(
                name="Lead_Investigator",
                llm_config=self.llm_config, # No tools needed, just logic
                system_message="""You are the Lead Investigator. 
                1. Analyze the user's objective.
                2. Delegate specific tasks to the Tool_Specialist.
                3. Synthesize the findings into a final report.
                4. When finished, reply with 'TERMINATE'.
                Do not ask the Admin to run tools directly, ask the Tool_Specialist to help you."""
            )
            
            # TOOL SPECIALIST
            tool_list = [t['name'] for t in self.tool_registry.get_tool_definitions()]
            tool_list_str = ", ".join(tool_list)
            
            specialist = autogen.AssistantAgent(
                name="Tool_Specialist",
                llm_config=agent_llm_config, # Has function definitions
                system_message=f"""You are the Tool Specialist.
                You have access to the following OSINT tools: {tool_list_str}.
                When the Lead Investigator asks for info, choose the right tool and call 'run_osint_tool'.
                Analyze the output and report back to the Lead. NEVER output Raw JSON, summarize it."""
            )

            # --- 3. Hook for Real-Time Updates ---
            if update_callback:
                def print_callback(recipient, messages, sender, config):
                    if "callback" in config and  config["callback"] is not None:
                        callback = config["callback"]
                        callback(sender, recipient, messages[-1])
                    return False, None # Pass through

                # Register reply hooks to capture messages
                # Note: This is an experimental way to hook into AutoGen's flow
                user_proxy.register_reply([autogen.Agent, None], print_callback, config={"callback": update_callback})
                leader.register_reply([autogen.Agent, None], print_callback, config={"callback": update_callback})
                specialist.register_reply([autogen.Agent, None], print_callback, config={"callback": update_callback})


            # --- 4. Start Group Chat ---
            groupchat = autogen.GroupChat(
                agents=[user_proxy, leader, specialist], 
                messages=[], 
                max_round=15
            )
            
            manager = autogen.GroupChatManager(
                groupchat=groupchat, 
                llm_config=self.llm_config
            )

            # --- 5. Start ---
            logger.info(f"Starting Multi-Agent GroupChat: {objective}")
            
            user_proxy.initiate_chat(
                manager,
                message=f"Investigation Objective: {objective}"
            )
            
            # Extract History
            # The manager holds the group chat history
            history = groupchat.messages
            
            # Format history for display
            formatted_log = ""
            for msg in history:
                name = msg.get('name', 'Unknown')
                content = msg.get('content', '')
                # Skip tool calls/function requests in the summary if they are verbose
                if "function_call" in msg:
                    continue
                formatted_log += f"\n**{name}**: {content}\n"
                
            return formatted_log
            
        except Exception as e:
            logger.error(f"AutoGen Error: {e}")
            return f"The Multi-Agent team encountered an error: {e}"
