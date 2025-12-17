"""Modules package for AthenaOSINT."""

from typing import Dict, Any


def get_available_modules() -> Dict[str, Dict[str, Any]]:
    """Get information about all available modules.
    
    Returns:
        Dictionary mapping module names to their info
    """
    modules = {
        'sherlock': {
            'description': 'Username enumeration across 300+ social media sites',
            'target_type': 'username',
            'requirements': 'sherlock-project',
            'available': False
        },
        'holehe': {
            'description': 'Email account discovery across services',
            'target_type': 'email',
            'requirements': 'holehe',
            'available': False
        },
        'theharvester': {
            'description': 'Email and domain reconnaissance',
            'target_type': 'domain, email',
            'requirements': 'theHarvester CLI tool',
            'available': False
        },
        'subfinder': {
            'description': 'Subdomain enumeration',
            'target_type': 'domain',
            'requirements': 'subfinder CLI tool',
            'available': False
        },
        'leak_checker': {
            'description': 'Data breach search (HIBP, Dehashed, IntelX)',
            'target_type': 'email',
            'requirements': 'API keys',
            'available': True
        },
        'exiftool': {
            'description': 'File metadata extraction',
            'target_type': 'file',
            'requirements': 'exiftool CLI tool',
            'available': False
        },
        'socialscan': {
            'description': 'Social media username availability checker',
            'target_type': 'username, email',
            'requirements': 'socialscan',
            'available': False
        },
        'dnsdumpster': {
            'description': 'DNS records and network mapping',
            'target_type': 'domain',
            'requirements': 'None (Scraper)',
            'available': False
        },
        'amass': {
            'description': 'Advanced subdomain enumeration',
            'target_type': 'domain',
            'requirements': 'amass CLI',
            'available': False
        },
        'nuclei': {
            'description': 'Vulnerability scanner',
            'target_type': 'domain',
            'requirements': 'nuclei CLI',
            'available': False
        },
        'foca': {
            'description': 'Document metadata analysis',
            'target_type': 'domain',
            'requirements': 'None (Scraper)',
            'available': False
        },
        'profile_scraper': {
            'description': 'Social media bio & link extraction',
            'target_type': 'username',
            'requirements': 'None (Scraper)',
            'available': False
        },
        'auto_dorker': {
            'description': 'Google Dork generator',
            'target_type': 'domain, username',
            'requirements': 'None',
            'available': False
        },
        'wayback': {
            'description': 'Internet Archive historic checker',
            'target_type': 'domain',
            'requirements': 'None',
            'available': False
        },
        'crypto_hunter': {
            'description': 'Cryptocurrency address scanner',
            'target_type': 'any',
            'requirements': 'None',
            'available': False
        },
        'cloud_hunter': {
            'description': 'Public cloud bucket scanner',
            'target_type': 'domain',
            'requirements': 'None',
            'available': False
        },
        'sentiment': {
            'description': 'AI Sentiment Analysis',
            'target_type': 'profile',
            'requirements': 'None (AI)',
            'available': False
        }
    }
    
    # Check availability of each module
    for module_name in modules.keys():
        try:
            __import__(f'modules.{module_name}')
            modules[module_name]['available'] = True
        except ImportError:
            pass
    
    return modules


__all__ = ['get_available_modules']
