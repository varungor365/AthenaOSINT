"""
Email Permutator Module.
Generates potential email addresses from a name and domain.
"""

from typing import List
from colorama import Fore, Style
from core.engine import Profile

META = {
    'description': 'Generates email permutations for a target',
    'target_type': 'username, domain',
    'requirements': 'None'
}

def generate_permutations(first: str, last: str, domain: str) -> List[str]:
    """Generate common email permutations."""
    f = first.lower()
    l = last.lower()
    d = domain.lower()
    
    perms = [
        f"{f}@{d}",                 # john@
        f"{l}@{d}",                 # doe@
        f"{f}{l}@{d}",              # johndoe@
        f"{f}.{l}@{d}",             # john.doe@
        f"{f}_{l}@{d}",             # john_doe@
        f"{l}{f}@{d}",              # doejohn@
        f"{l}.{f}@{d}",             # doe.john@
        f"{f[0]}{l}@{d}",           # jdoe@
        f"{f[0]}.{l}@{d}",          # j.doe@
        f"{f}{l[0]}@{d}",           # johnd@
        f"{f}.{l[0]}@{d}",          # john.d@
        f"{f[0]}{l[0]}@{d}",        # jd@
    ]
    return perms

def scan(target: str, profile: Profile) -> None:
    """Run the email permutator."""
    print(f"{Fore.CYAN}[+] Running Email Permutator...{Style.RESET_ALL}")
    
    # Need context: First/Last name.
    # We try to guess from the target if it looks like "john.doe" or "johndoe"
    # Or check if we have resolved identity data in the profile
    
    parts = []
    domain = "gmail.com" # Default fallback
    
    # Heuristic: Try to split target by space or dot
    if " " in target:
        parts = target.split(" ")
    elif "." in target:
        parts = target.split(".")
        
    # Check for domain in profile
    if profile.domains:
        domain = profile.domains[0]
    elif "@" in target:
       # If target is email, use that domain
       domain = target.split("@")[1]
       target = target.split("@")[0]
       # Re-split name part
       if "." in target: parts = target.split(".")
    
    if len(parts) >= 2:
        first, last = parts[0], parts[1]
        print(f"  {Fore.BLUE}ℹ Identity guessed: {first} {last} @ {domain}{Style.RESET_ALL}")
        
        emails = generate_permutations(first, last, domain)
        
        print(f"  {Fore.GREEN}└─ Generated {len(emails)} permutations:{Style.RESET_ALL}")
        
        # In a real tool, we would verify these via SMTP 
        # (RCPT TO check, but that's risky and often blocked).
        # We will just list them for now.
        
        valid_emails = []
        for email in emails:
            # Placeholder for SMTP check
            # if verify_smtp(email): ...
            valid_emails.append(email)
            print(f"     - {email}")
            
        # Add to profile
        for email in valid_emails:
            if email not in profile.emails:
                profile.emails.append(email) 
    else:
        print(f"  {Fore.YELLOW}└─ Could not parse First/Last name from target '{target}' for permutations.{Style.RESET_ALL}")

