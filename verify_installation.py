"""
Verification Script for AthenaOSINT.
Checks if all modules can be imported and initialized.
"""
import sys
import os
import importlib
import traceback
from colorama import Fore, Style, init

init(autoreset=True)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MODULES_TO_CHECK = [
    'config.config',
    'core.engine',
    'core.api_manager',
    'core.health_monitor',
    'modules.sherlock',
    'modules.theharvester',
    'modules.holehe',
    'modules.subfinder',
    'modules.leak_checker',
    'modules.dnsdumpster',
    'modules.amass',
    'modules.nuclei',
    'modules.foca',
    'modules.profile_scraper',
    'modules.crypto_hunter',
    'modules.cloud_hunter',
    'modules.sentiment',
    'modules.wayback',
    'modules.auto_dorker',
    'modules.exiftool',
    'intelligence.analyzer',
    'intelligence.automator',
    'intelligence.llm',
    'intelligence.identity_resolver',
    'web.routes',
    'bot.bot_handler',
    'athena'
]

def verify_modules():
    print(f"{Fore.CYAN}Starting System Verification...{Style.RESET_ALL}\n")
    errors = []
    
    for module_name in MODULES_TO_CHECK:
        try:
            print(f"Checking {module_name}...", end=' ')
            importlib.import_module(module_name)
            print(f"{Fore.GREEN}OK{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}FAILED{Style.RESET_ALL}")
            error_msg = f"{module_name}: {str(e)}"
            errors.append(error_msg)
            # traceback.print_exc()

    print(f"\n{Fore.CYAN}Verification Complete.{Style.RESET_ALL}")
    
    if errors:
        print(f"\n{Fore.RED}Found {len(errors)} errors:{Style.RESET_ALL}")
        for err in errors:
            print(f" - {err}")
        sys.exit(1)
    else:
        print(f"\n{Fore.GREEN}All systems operational.{Style.RESET_ALL}")
        sys.exit(0)

if __name__ == "__main__":
    verify_modules()
