"""
Identity Resolver for AthenaOSINT.

This module performs cross-referencing of collected data to resolve
identities with high accuracy and confidence.
"""

from typing import Dict, List, Any, Set
from loguru import logger
import hashlib

from core.engine import Profile

class IdentityResolver:
    """Resolves and correlates identity information."""
    
    def __init__(self):
        """Initialize resolver."""
        pass
        
    def resolve_identity(self, profile: Profile) -> Dict[str, Any]:
        """Process profile to calculate identity confidence.
        
        Args:
            profile: Profile object
            
        Returns:
            Dictionary with resolution details and score
        """
        logger.info(f"Resolving identity for {profile.target_query}")
        
        resolution = {
            'confidence_score': 0.0,
            'confirmed_attributes': [],
            'conflicts': [],
            'primary_persona': {}
        }
        
        # 1. Cross-Platform Username Correlation
        # If username 'jdoe' exists on both GitHub and Twitter, confidence +
        self._check_platform_correlation(profile, resolution)
        
        # 2. Bio/Location Matching
        # If Bio works were scraped, check similarity
        self._check_content_similarity(profile, resolution)
        
        # 3. Email Confirmation
        # If emails were found and validated (by holehe/leak_checker)
        if profile.emails:
            resolution['confidence_score'] += 20
            resolution['confirmed_attributes'].append(f"Verified Emails: {len(profile.emails)}")
            
        # Cap score
        resolution['confidence_score'] = min(100.0, resolution['confidence_score'])
        
        # Store in raw_data
        profile.raw_data['identity_resolution'] = resolution
        
        return resolution
        
    def _check_platform_correlation(self, profile: Profile, resolution: Dict):
        """Check for consistent username usage."""
        count = len(profile.usernames)
        if count > 1:
            resolution['confidence_score'] += (count * 5) # 5 points per platform
            resolution['confirmed_attributes'].append(f"Active on {count} platforms")
            
        # Specific high-value combinations
        platforms = [p.lower() for p in profile.usernames.keys()]
        if 'github' in platforms and 'twitter' in platforms:
             resolution['confidence_score'] += 10
             resolution['confirmed_attributes'].append("Dev/Public Persona Link (GH+Twitter)")

    def _check_content_similarity(self, profile: Profile, resolution: Dict):
        """Check if scraped bios/locations match."""
        details = profile.raw_data.get('social_details', {})
        if not details:
            return
            
        locations = []
        for site, data in details.items():
            loc = data.get('location')
            if loc:
                locations.append(loc)
                
        # Simple exact match check for now
        # In real world, use fuzzy matching or AI
        if len(locations) > 1:
            # Check for overlaps
            unique_locs = set(locations)
            if len(unique_locs) < len(locations):
                # We have duplicates, meaning confirmation!
                resolution['confidence_score'] += 15
                resolution['confirmed_attributes'].append(f"Consistent Location: {locations[0]}")
