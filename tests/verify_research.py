
import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_research_flow():
    print("[-] Setting up mock environment...")
    
    # Mock Config
    os.environ['OPENAI_API_KEY'] = 'sk-test-key-mock'
    
    # Pre-mock autogen in sys.modules to avoid ImportError if not installed
    mock_autogen = MagicMock()
    sys.modules['autogen'] = mock_autogen
    
    # Setup specific mocks
    mock_user = MagicMock()
    mock_user.name = "Commander_Admin"
    mock_assistant = MagicMock() 
    mock_assistant.name = "Lead_Investigator"
    mock_groupchat = MagicMock()
    mock_groupchat.messages = [{"role": "user", "content": "test", "name": "Commander_Admin"}]
    mock_manager = MagicMock()
    
    mock_autogen.UserProxyAgent.return_value = mock_user
    mock_autogen.AssistantAgent.return_value = mock_assistant
    mock_autogen.GroupChat.return_value = mock_groupchat
    mock_autogen.GroupChatManager.return_value = mock_manager
    mock_autogen.Agent = MagicMock
    
    # Now import the wrapper
    print("[-] Importing MultiAgentSystem...")
    from intelligence.autogen_wrapper import MultiAgentSystem
    
    # Initialize
    mas = MultiAgentSystem()
    if not mas.enabled:
        print("[X] System disabled despite mock key!")
        return
        
    print("[+] System enabled.")
    
    # Run Investigation
    print("[-] Running investigation...")
    callback_mock = MagicMock()
    
    mas.run_investigation("Investigate 127.0.0.1", update_callback=callback_mock)
    
    # Verifications
    print("[+] Verifying logic...")
    mock_autogen.UserProxyAgent.assert_called()
    mock_user.initiate_chat.assert_called()
    
    # Verify Callback Registration
    # Check if register_reply was called
    if mock_user.register_reply.called:
        print("[+] Callback hooks registered successfully.")
    else:
        print("[!] Warning: register_reply not called.")
        
    print("[SUCCESS] Research Mode logic verified.")

if __name__ == "__main__":
    test_research_flow()
