"""
Holehe module for AthenaOSINT.

This module integrates Holehe for email account discovery
across various online services.
"""

import asyncio
from typing import Dict, Any
from colorama import Fore, Style
from loguru import logger

try:
    import holehe
    from holehe.modules import *
    from holehe.core import * 
    HOLEHE_AVAILABLE = True
except ImportError:
    HOLEHE_AVAILABLE = False
    logger.warning("Holehe library not available. Install with: pip install holehe")


def scan(target: str, profile) -> None:
    """Scan for email accounts across services.
    
    Args:
        target: Email address to check
        profile: Profile object to update with results
    """
    if not HOLEHE_AVAILABLE:
        logger.warning("Holehe module skipped - library not installed")
        profile.add_error('holehe', 'Library not installed')
        return
    
    from core.validators import validate_email
    
    if not validate_email(target):
        logger.warning(f"Holehe module skipped - target '{target}' is not a valid email")
        return
    
    print(f"{Fore.CYAN}[+] Running Holehe module...{Style.RESET_ALL}")
    
    try:
        # Run Holehe scan asynchronously
        results = asyncio.run(_run_holehe(target))
        
        # Process results
        found_services = []
        for service_name, service_data in results.items():
            if service_data.get('exists', False):
                # Add to profile
                profile.add_username(service_name, target)
                profile.add_email(target)
                found_services.append(service_name)
        
        # Store raw data
        profile.raw_data['holehe'] = {
            'email': target,
            'services_checked': len(results),
            'services_found': len(found_services),
            'results': results
        }
        
        print(f"{Fore.GREEN}[✓] Holehe found accounts on {len(found_services)} services{Style.RESET_ALL}")
        logger.info(f"Holehe scan complete: {len(found_services)} services found")
        
    except Exception as e:
        error_msg = f"Holehe scan failed: {str(e)}"
        logger.error(error_msg)
        profile.add_error('holehe', str(e))
        print(f"{Fore.RED}[✗] {error_msg}{Style.RESET_ALL}")


async def _run_holehe(email: str) -> Dict[str, Any]:
    """Run Holehe scan asynchronously.
    
    Args:
        email: Email to check
        
    Returns:
        Dictionary of results by service
    """
    try:
        # Import all Holehe modules
        import holehe.modules
        import importlib
        import pkgutil
        
        results = {}
        
        # Discover all Holehe modules
        holehe_modules = []
        for importer, modname, ispkg in pkgutil.iter_modules(holehe.modules.__path__):
            try:
                module = importlib.import_module(f'holehe.modules.{modname}')
                if hasattr(module, modname):
                    holehe_modules.append((modname, getattr(module, modname)))
            except:
                continue
        
        # Run each module
        for service_name, service_fn in holehe_modules:
            try:
                result = await service_fn(email, client=None, out=[])
                results[service_name] = {
                    'exists': result.get('exists', False) if isinstance(result, dict) else False,
                    'rateLimit': result.get('rateLimit', False) if isinstance(result, dict) else False,
                    'data': result
                }
            except Exception as e:
                logger.debug(f"Holehe module {service_name} failed: {e}")
                results[service_name] = {
                    'exists': False,
                    'error': str(e)
                }
        
        return results
        
    except Exception as e:
        logger.error(f"Holehe async execution failed: {e}")
        return {}
