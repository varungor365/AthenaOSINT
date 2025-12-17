"""
Risk Calculator.
Analyzes OSINT findings to calculate a Risk/Threat Score (0-100).
"""

from core.engine import Profile

class RiskCalculator:
    """Calculates risk score based on findings."""
    
    def calculate(self, profile: Profile) -> dict:
        """
        Calculate risk score.
        
        Criteria:
        - Leaked Password (Plaintext): +25
        - Leaked Hash: +15
        - Open Cloud Bucket: +30
        - Vulnerability (High): +20
        - Exposed API Key: +40
        - Honeytoken Triggered: +50
        - Personal Email Found: +5
        - Phone Number Found: +10
        """
        score = 0
        breakdown = []
        
        # 1. Breach Data
        if profile.raw_data.get('local_intelligence'):
            hits = profile.raw_data['local_intelligence']
            for hit in hits:
                if 'password' in hit['type'] or 'hash' in hit['type']:
                    score += 25
                    breakdown.append("Leaked Credential Discovery (+25)")
                    break # Cap per category
        
        # 2. Cloud Buckets
        if 'cloud_buckets' in profile.raw_data:
            score += 30
            breakdown.append("Open Cloud Storage Buckets (+30)")
            
        # 3. Emails/Phones
        if len(profile.emails) > 2:
            score += 10
            breakdown.append("Multiple Email Identities (+10)")
        if profile.phones:
            score += 15
            breakdown.append("Phone Number Exposure (+15)")
            
        # 4. Critical Alerts (Honeytokens, etc)
        alerts = profile.raw_data.get('alerts', [])
        if alerts:
            score += 20
            breakdown.append(f"Security Alerts Triggered ({len(alerts)}) (+20)")
            
        # Cap at 100
        score = min(score, 100)
        
        # Rating
        rating = "LOW"
        color = "green"
        if score > 30: 
            rating = "MEDIUM"
            color = "orange"
        if score > 60: 
            rating = "HIGH"
            color = "red"
        if score > 85: 
            rating = "CRITICAL"
            color = "darkred"
            
        return {
            'score': score,
            'rating': rating,
            'color': color,
            'breakdown': breakdown
        }
