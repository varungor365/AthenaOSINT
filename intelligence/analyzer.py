"""
Intelligence Analyzer for AthenaOSINT.

This module provides intelligent analysis of scan results to discover
patterns, correlations, and new investigation leads.
"""

import re
from typing import List, Dict, Set, Any
from loguru import logger
from core.validators import extract_domain_from_email, validate_domain, validate_username


class IntelligenceAnalyzer:
    """Analyzes OSINT data to find patterns and new leads."""
    
    def __init__(self):
        """Initialize the intelligence analyzer."""
        self.patterns = {
            'year_suffix': re.compile(r'(\d{2,4})$'),
            'number_suffix': re.compile(r'(\d+)$'),
            'separator': re.compile(r'[._-]'),
            'leet_speak': {
                'a': ['4', '@'],
                'e': ['3'],
                'i': ['1', '!'],
                'o': ['0'],
                's': ['5', '$'],
                't': ['7']
            }
        }
    
    def analyze_profile(self, profile) -> Dict[str, Any]:
        """Analyze a profile to find intelligence and new leads.
        
        Args:
            profile: Profile object to analyze
            
        Returns:
            Dictionary containing analysis results and new targets
        """
        logger.info(f"Starting intelligence analysis on {profile.target_query}")
        
        analysis = {
            'related_domains': set(),
            'username_variations': set(),
            'related_entities': [],
            'password_patterns': {},
            'risk_score': 0,
            'insights': []
        }
        
        # Entity correlation
        self._correlate_entities(profile, analysis)
        
        # Username pattern recognition
        self._analyze_username_patterns(profile, analysis)
        
        # Password policy inference
        self._infer_password_policies(profile, analysis)
        
        # Relationship mapping
        self._map_relationships(profile, analysis)
        
        # Calculate risk score
        analysis['risk_score'] = self._calculate_risk_score(profile, analysis)
        
        # AI Analysis (New)
        try:
            from intelligence.llm import LLMClient
            llm_client = LLMClient()
            ai_insights = llm_client.analyze_profile(profile.to_dict())
            
            if 'error' not in ai_insights:
                analysis['ai_insights'] = ai_insights.get('summary', '')
                analysis['insights'].extend(ai_insights.get('key_findings', []))
                
                # Merge new targets from AI
                ai_suggestions = ai_insights.get('suggested_actions', [])
                for suggestion in ai_suggestions:
                    # simplistic extraction of potential targets from text suggestions
                    # In a real scenario, we'd ask LLM for structured target list
                    pass
                
                logger.info("AI analysis completed successfully")
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")

        # Store analysis results in profile
        profile.raw_data['intelligence_analysis'] = {
            'related_domains': list(analysis['related_domains']),
            'username_variations': list(analysis['username_variations']),
            'insights': analysis['insights'],
            'risk_score': analysis['risk_score']
        }
        
        # Add related entities to profile
        for entity in analysis['related_entities']:
            profile.related_entities.append(entity)
        
        logger.info(f"Intelligence analysis complete. Risk score: {analysis['risk_score']}/100")
        
        return analysis
    
    def _correlate_entities(self, profile, analysis: Dict[str, Any]):
        """Find correlations between different data points.
        
        Args:
            profile: Profile to analyze
            analysis: Analysis results dict to update
        """
        # Extract domains from emails
        for email in profile.emails:
            domain = extract_domain_from_email(email)
            if domain and validate_domain(domain):
                analysis['related_domains'].add(domain)
                analysis['insights'].append(f"Domain '{domain}' extracted from email")
        
        # Look for patterns in usernames
        username_domains = set()
        for platform, username in profile.usernames.items():
            # Check if username contains domain hints
            for domain in analysis['related_domains']:
                domain_parts = domain.split('.')
                for part in domain_parts:
                    if len(part) > 3 and part.lower() in username.lower():
                        username_domains.add(domain)
                        analysis['insights'].append(
                            f"Username '{username}' may be related to domain '{domain}'"
                        )
        
        analysis['related_domains'].update(username_domains)
        
        # Cross-reference breaches with domains
        breach_domains = set()
        for breach in profile.breaches:
            breach_domain = breach.get('domain', '')
            if breach_domain and validate_domain(breach_domain):
                breach_domains.add(breach_domain)
        
        analysis['related_domains'].update(breach_domains)
    
    def _analyze_username_patterns(self, profile, analysis: Dict[str, Any]):
        """Generate username variations based on patterns.
        
        Args:
            profile: Profile to analyze
            analysis: Analysis results dict to update
        """
        base_usernames = set(profile.usernames.values())
        
        # Add target if it looks like a username
        if validate_username(profile.target_query):
            base_usernames.add(profile.target_query)
        
        for username in base_usernames:
            variations = self._generate_username_variations(username)
            analysis['username_variations'].update(variations)
        
        logger.info(f"Generated {len(analysis['username_variations'])} username variations")
    
    def _generate_username_variations(self, username: str) -> Set[str]:
        """Generate possible variations of a username.
        
        Args:
            username: Base username
            
        Returns:
            Set of username variations
        """
        variations = set()
        base = username.lower()
        
        # Remove existing numbers/years
        year_match = self.patterns['year_suffix'].search(base)
        if year_match:
            base_no_year = base[:year_match.start()]
            year = year_match.group(1)
            
            # Try different years
            current_year = 2025
            for y in range(current_year - 10, current_year + 1):
                variations.add(f"{base_no_year}{y}")
                variations.add(f"{base_no_year}{str(y)[2:]}")  # Last 2 digits
        
        # Try common number suffixes
        for num in ['1', '2', '12', '123', '01', '21', '89', '99']:
            variations.add(f"{base}{num}")
        
        # Try with different separators
        for sep in ['', '.', '_', '-']:
            parts = self.patterns['separator'].split(username)
            if len(parts) > 1:
                variations.add(sep.join(parts))
        
        # Leet speak variations
        leet_variations = self._apply_leet_speak(base)
        variations.update(leet_variations)
        
        # Capitalize variations
        variations.add(username.capitalize())
        variations.add(username.upper())
        
        return variations
    
    def _apply_leet_speak(self, text: str) -> Set[str]:
        """Apply leet speak transformations.
        
        Args:
            text: Text to transform
            
        Returns:
            Set of leet speak variations
        """
        variations = set()
        
        # Simple leet speak: replace one character
        for char, replacements in self.patterns['leet_speak'].items():
            if char in text.lower():
                for replacement in replacements:
                    variation = text.lower().replace(char, replacement, 1)
                    variations.add(variation)
        
        return variations
    
    def _infer_password_policies(self, profile, analysis: Dict[str, Any]):
        """Infer password policies from breached passwords.
        
        Args:
            profile: Profile to analyze
            analysis: Analysis results dict to update
        """
        passwords = []
        
        # Extract passwords from breach data
        for breach in profile.breaches:
            if 'password' in breach and breach['password'] != '[REDACTED]':
                passwords.append(breach['password'])
        
        if not passwords:
            return
        
        policies = {
            'min_length': float('inf'),
            'max_length': 0,
            'requires_uppercase': False,
            'requires_lowercase': False,
            'requires_numbers': False,
            'requires_special': False,
            'common_patterns': []
        }
        
        for pwd in passwords:
            if not pwd:
                continue
            
            # Length
            policies['min_length'] = min(policies['min_length'], len(pwd))
            policies['max_length'] = max(policies['max_length'], len(pwd))
            
            # Character requirements
            if any(c.isupper() for c in pwd):
                policies['requires_uppercase'] = True
            if any(c.islower() for c in pwd):
                policies['requires_lowercase'] = True
            if any(c.isdigit() for c in pwd):
                policies['requires_numbers'] = True
            if any(not c.isalnum() for c in pwd):
                policies['requires_special'] = True
        
        if policies['min_length'] != float('inf'):
            analysis['password_patterns'] = policies
            analysis['insights'].append(
                f"Inferred password policy: min {policies['min_length']} chars, "
                f"requires: {'uppercase ' if policies['requires_uppercase'] else ''}"
                f"{'numbers ' if policies['requires_numbers'] else ''}"
                f"{'special chars' if policies['requires_special'] else ''}"
            )
    
    def _map_relationships(self, profile, analysis: Dict[str, Any]):
        """Map relationships between entities.
        
        Args:
            profile: Profile to analyze
            analysis: Analysis results dict to update
        """
        # Create entity relationships
        for email in profile.emails:
            domain = extract_domain_from_email(email)
            if domain:
                analysis['related_entities'].append({
                    'type': 'email_to_domain',
                    'source': email,
                    'target': domain,
                    'relationship': 'belongs_to'
                })
        
        # Username to platform relationships
        for platform, username in profile.usernames.items():
            analysis['related_entities'].append({
                'type': 'username_to_platform',
                'source': username,
                'target': platform,
                'relationship': 'has_account_on'
            })
        
        # Breach to email relationships
        for breach in profile.breaches:
            for email in profile.emails:
                analysis['related_entities'].append({
                    'type': 'email_to_breach',
                    'source': email,
                    'target': breach.get('name', 'Unknown'),
                    'relationship': 'compromised_in',
                    'date': breach.get('date', '')
                })
    
    def _calculate_risk_score(self, profile, analysis: Dict[str, Any]) -> int:
        """Calculate overall risk score for the target.
        
        Args:
            profile: Profile to analyze
            analysis: Analysis results
            
        Returns:
            Risk score from 0-100
        """
        score = 0
        
        # Breaches contribute heavily to risk
        score += min(len(profile.breaches) * 15, 50)
        
        # Multiple email addresses
        score += min(len(profile.emails) * 5, 15)
        
        # Extensive online presence
        score += min(len(profile.usernames) * 2, 20)
        
        # Leaked passwords
        for breach in profile.breaches:
            if breach.get('password') and breach['password'] != '[REDACTED]':
                score += 10
                break
        
        # Sensitive breaches
        for breach in profile.breaches:
            if breach.get('sensitive', False):
                score += 5
        
        return min(score, 100)
    
    def get_new_targets(self, profile, max_targets: int = 10) -> List[str]:
        """Get list of new targets to investigate based on analysis.
        
        Args:
            profile: Profile that was analyzed
            max_targets: Maximum number of targets to return
            
        Returns:
            List of new investigation targets
        """
        targets = []
        
        # Get analysis from raw_data
        analysis = profile.raw_data.get('intelligence_analysis', {})
        
        # Add related domains
        domains = analysis.get('related_domains', [])
        targets.extend(domains[:max_targets // 2])
        
        # Add username variations
        variations = analysis.get('username_variations', [])
        targets.extend(list(variations)[:max_targets // 2])
        
        # Remove duplicates and limit
        return list(set(targets))[:max_targets]
