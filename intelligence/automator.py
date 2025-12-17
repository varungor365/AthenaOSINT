"""
Automator module for AthenaOSINT.

This module handles recursive chain scanning, effectively "automating" the investigation
by using results from one scan as targets for the next.
"""

import time
from typing import Set, List, Dict
from loguru import logger
from colorama import Fore, Style

from core.engine import AthenaEngine, Profile
from core.validators import detect_target_type

class Automator:
    """Recursive scanning automation engine."""
    
    def __init__(self, max_depth: int = 2, quiet: bool = False):
        """Initialize Automator.
        
        Args:
            max_depth: Maximum recursion depth
            quiet: Suppress output
        """
        self.max_depth = max_depth
        self.quiet = quiet
        self.scanned_targets: Set[str] = set()
        self.all_profiles: List[Profile] = []
        
    def run_automated_chain(self, initial_target: str) -> List[Profile]:
        """Run the recursive scan chain.
        
        Args:
            initial_target: Starting target
            
        Returns:
            List of all profiles generated
        """
        queue = [(initial_target, 0)] # (target, depth)
        
        print(f"{Fore.MAGENTA}╔════════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}║      Athena Recursive Automator v1.0       ║{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}╚════════════════════════════════════════════╝{Style.RESET_ALL}")
        
        while queue:
            current_target, depth = queue.pop(0)
            
            if current_target in self.scanned_targets:
                continue
            
            if depth > self.max_depth:
                continue
            
            self._print_banner(current_target, depth)
            
            # 1. Run Standard Scan
            try:
                # Determine modules based on target type
                target_type = detect_target_type(current_target)
                modules = self._select_modules_for_type(target_type)
                
                engine = AthenaEngine(
                    target_query=current_target,
                    target_type=target_type,
                    use_intelligence=True,
                    quiet=self.quiet
                )
                
                engine.run_scan(modules)
                self.scanned_targets.add(current_target)
                self.all_profiles.append(engine.profile)
                
                # 2. Extract New Targets (if depth allows)
                if depth < self.max_depth:
                    new_targets = self._extract_new_leads(engine.profile)
                    
                    for lead in new_targets:
                        if lead not in self.scanned_targets:
                            queue.append((lead, depth + 1))
                            print(f"{Fore.CYAN}  [+] Added new lead to queue: {lead}{Style.RESET_ALL}")
                            
            except Exception as e:
                logger.error(f"Automator failed on {current_target}: {e}")
                print(f"{Fore.RED}[!] Automated scan failed for {current_target}{Style.RESET_ALL}")
                
        return self.all_profiles

    def _select_modules_for_type(self, target_type: str) -> List[str]:
        """Select appropriate modules based on target type."""
        # Core defaults
        modules = ['leak_checker']
        
        if target_type == 'username':
            modules.extend(['sherlock', 'profile_scraper'])
        elif target_type == 'email':
            modules.extend(['holehe', 'sherlock']) # Check username part of email?
        elif target_type == 'domain':
            modules.extend(['subfinder', 'dnsdumpster', 'amass', 'nuclei', 'foca'])
            
        return modules

    def _extract_new_leads(self, profile: Profile) -> Set[str]:
        """Extract potential new targets from a profile result."""
        leads = set()
        
        # Add found emails
        for email in profile.emails:
            leads.add(email)
            
        # Add found subdomains (limit to avoiding explosion)
        for subdomain in profile.subdomains[:5]: # limit to top 5
            leads.add(subdomain)
            
        # Add identity resolution findings (related accounts)
        # e.g. if we found a new username handle in a bio
        
        return leads

    def _print_banner(self, target: str, depth: int):
        if self.quiet: return
        indent = "  " * depth
        print(f"\n{indent}{Fore.YELLOW}► Automator: Scanning '{target}' (Depth {depth}/{self.max_depth}){Style.RESET_ALL}")
