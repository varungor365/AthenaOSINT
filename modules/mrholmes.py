"""
Mr.Holmes Integration Module
Unified OSINT tool for usernames, emails, phones, and domains
GitHub: https://github.com/Lucksi/Mr.Holmes
"""

import subprocess
import json
import re
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

class MrHolmes:
    """Mr.Holmes OSINT scanner wrapper"""
    
    def __init__(self):
        self.name = "Mr.Holmes"
        self.description = "Complete OSINT tool for usernames, emails, phones, and domains"
        self.repo_url = "https://github.com/Lucksi/Mr.Holmes"
        self.install_dir = Path.home() / ".mrholmes"
        self.mrholmes_script = self.install_dir / "MrHolmes.py"
        
    def is_installed(self) -> bool:
        """Check if Mr.Holmes is installed"""
        return self.mrholmes_script.exists()
    
    def install(self) -> bool:
        """Install Mr.Holmes from GitHub"""
        try:
            if self.is_installed():
                logger.info(f"Mr.Holmes already installed at {self.install_dir}")
                return True
            
            logger.info("Installing Mr.Holmes...")
            
            # Clone repository
            subprocess.run([
                "git", "clone", 
                "https://github.com/Lucksi/Mr.Holmes.git",
                str(self.install_dir)
            ], check=True, capture_output=True)
            
            # Install dependencies
            requirements = self.install_dir / "requirements.txt"
            if requirements.exists():
                subprocess.run([
                    "pip3", "install", "-r", str(requirements)
                ], check=True, capture_output=True)
            
            logger.success(f"Mr.Holmes installed successfully at {self.install_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install Mr.Holmes: {e}")
            return False
    
    def search_username(self, username: str, use_proxy: bool = False) -> Dict:
        """
        Search for username across social media platforms
        
        Args:
            username: Target username to search
            use_proxy: Whether to use proxy (not implemented in automated mode)
            
        Returns:
            Dictionary with found profiles, scraped data, and metadata
        """
        if not self.is_installed():
            if not self.install():
                return {"error": "Mr.Holmes not installed"}
        
        result = {
            "target": username,
            "target_type": "username",
            "profiles_found": [],
            "social_accounts": {},
            "scraped_data": {},
            "report_files": [],
            "raw_output": ""
        }
        
        try:
            # Mr.Holmes stores reports in GUI/Reports/Usernames/{username}/
            report_dir = self.install_dir / "GUI" / "Reports" / "Usernames" / username
            
            # Clean old reports
            if report_dir.exists():
                shutil.rmtree(report_dir)
            
            # Run Mr.Holmes username search
            # Note: Mr.Holmes is interactive by default, we'll parse the output
            logger.info(f"Running Mr.Holmes username search for: {username}")
            
            # For now, we'll use a simulated approach since Mr.Holmes is interactive
            # In production, you'd need to modify Mr.Holmes or use expect/pexpect
            result["info"] = "Mr.Holmes requires interactive mode. Please use the web interface to configure searches."
            result["status"] = "pending_interactive"
            
            # TODO: Implement automated search using pexpect or API mode
            # For now, return installation status and manual instructions
            result["instructions"] = f"""
            To use Mr.Holmes:
            1. Navigate to: {self.install_dir}
            2. Run: python3 MrHolmes.py
            3. Select option 1 for username search
            4. Enter username: {username}
            5. Results will be saved to: {report_dir}
            """
            
            return result
            
        except Exception as e:
            logger.error(f"Mr.Holmes username search failed: {e}")
            return {"error": str(e), "target": username}
    
    def search_email(self, email: str) -> Dict:
        """
        Search for email information and associated accounts
        
        Args:
            email: Target email to search
            
        Returns:
            Dictionary with email validation, breaches, and associated accounts
        """
        if not self.is_installed():
            if not self.install():
                return {"error": "Mr.Holmes not installed"}
        
        result = {
            "target": email,
            "target_type": "email",
            "valid": None,
            "breaches": [],
            "associated_accounts": [],
            "report_files": [],
            "raw_output": ""
        }
        
        try:
            report_dir = self.install_dir / "GUI" / "Reports" / "Emails" / email.replace("@", "_at_")
            
            result["info"] = "Mr.Holmes email search requires interactive mode"
            result["status"] = "pending_interactive"
            result["instructions"] = f"""
            To use Mr.Holmes for email:
            1. Navigate to: {self.install_dir}
            2. Run: python3 MrHolmes.py
            3. Select option 8 for email search
            4. Enter email: {email}
            5. Results will be saved to: {report_dir}
            """
            
            return result
            
        except Exception as e:
            logger.error(f"Mr.Holmes email search failed: {e}")
            return {"error": str(e), "target": email}
    
    def search_phone(self, phone: str) -> Dict:
        """
        Search for phone number information
        
        Args:
            phone: Target phone number (international format recommended)
            
        Returns:
            Dictionary with carrier, location, and associated accounts
        """
        if not self.is_installed():
            if not self.install():
                return {"error": "Mr.Holmes not installed"}
        
        result = {
            "target": phone,
            "target_type": "phone",
            "carrier": None,
            "location": None,
            "timezone": None,
            "associated_accounts": [],
            "report_files": [],
            "raw_output": ""
        }
        
        try:
            report_dir = self.install_dir / "GUI" / "Reports" / "Phone" / phone
            
            result["info"] = "Mr.Holmes phone search requires interactive mode"
            result["status"] = "pending_interactive"
            result["instructions"] = f"""
            To use Mr.Holmes for phone:
            1. Navigate to: {self.install_dir}
            2. Run: python3 MrHolmes.py
            3. Select option 2 for phone search
            4. Enter phone: {phone}
            5. Results will be saved to: {report_dir}
            """
            
            return result
            
        except Exception as e:
            logger.error(f"Mr.Holmes phone search failed: {e}")
            return {"error": str(e), "target": phone}
    
    def search_domain(self, domain: str) -> Dict:
        """
        Search for domain/website information
        
        Args:
            domain: Target domain to search
            
        Returns:
            Dictionary with WHOIS, DNS, and reputation data
        """
        if not self.is_installed():
            if not self.install():
                return {"error": "Mr.Holmes not installed"}
        
        result = {
            "target": domain,
            "target_type": "domain",
            "whois": {},
            "dns_records": [],
            "reputation": {},
            "associated_emails": [],
            "associated_phones": [],
            "report_files": [],
            "raw_output": ""
        }
        
        try:
            report_dir = self.install_dir / "GUI" / "Reports" / "Websites" / domain
            
            result["info"] = "Mr.Holmes domain search requires interactive mode"
            result["status"] = "pending_interactive"
            result["instructions"] = f"""
            To use Mr.Holmes for domain:
            1. Navigate to: {self.install_dir}
            2. Run: python3 MrHolmes.py
            3. Select option 3 for website search
            4. Enter domain: {domain}
            5. Results will be saved to: {report_dir}
            """
            
            return result
            
        except Exception as e:
            logger.error(f"Mr.Holmes domain search failed: {e}")
            return {"error": str(e), "target": domain}
    
    def get_results(self, target: str, target_type: str) -> Optional[Dict]:
        """
        Retrieve existing Mr.Holmes results for a target
        
        Args:
            target: The target that was searched
            target_type: Type of search (username, email, phone, domain)
            
        Returns:
            Parsed results from Mr.Holmes report files
        """
        try:
            # Determine report directory based on target type
            if target_type == "username":
                report_dir = self.install_dir / "GUI" / "Reports" / "Usernames" / target
            elif target_type == "email":
                report_dir = self.install_dir / "GUI" / "Reports" / "Emails" / target.replace("@", "_at_")
            elif target_type == "phone":
                report_dir = self.install_dir / "GUI" / "Reports" / "Phone" / target
            elif target_type == "domain":
                report_dir = self.install_dir / "GUI" / "Reports" / "Websites" / target
            else:
                return None
            
            if not report_dir.exists():
                return None
            
            # Parse report files
            result = {
                "target": target,
                "target_type": target_type,
                "reports": []
            }
            
            # Find all .txt report files
            for report_file in report_dir.glob("*.txt"):
                with open(report_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    result["reports"].append({
                        "file": report_file.name,
                        "content": content
                    })
            
            # Find JSON files if they exist
            for json_file in report_dir.glob("*.json"):
                with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                    try:
                        data = json.load(f)
                        result[json_file.stem] = data
                    except:
                        pass
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get Mr.Holmes results: {e}")
            return None


def scan(target: str, target_type: str = "auto", **kwargs) -> Dict:
    """
    Main entry point for Mr.Holmes scans
    
    Args:
        target: Target to search (username, email, phone, or domain)
        target_type: Type of target (auto-detect if not specified)
        **kwargs: Additional options
        
    Returns:
        Scan results dictionary
    """
    mrholmes = MrHolmes()
    
    # Auto-detect target type if not specified
    if target_type == "auto":
        if "@" in target:
            target_type = "email"
        elif "." in target and not target[0].isdigit():
            target_type = "domain"
        elif target[0] == "+":
            target_type = "phone"
        else:
            target_type = "username"
    
    logger.info(f"Running Mr.Holmes {target_type} search for: {target}")
    
    # Route to appropriate search function
    if target_type == "username":
        return mrholmes.search_username(target, kwargs.get("use_proxy", False))
    elif target_type == "email":
        return mrholmes.search_email(target)
    elif target_type == "phone":
        return mrholmes.search_phone(target)
    elif target_type == "domain":
        return mrholmes.search_domain(target)
    else:
        return {"error": f"Unknown target type: {target_type}"}
