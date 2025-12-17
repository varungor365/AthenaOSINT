"""Modules package for AthenaOSINT.

This package automatically discovers and loads all valid OSINT modules
in the current directory.
"""

import os
import importlib
import pkgutil
from typing import Dict, Any
from pathlib import Path
from loguru import logger

def get_available_modules() -> Dict[str, Dict[str, Any]]:
    """Dynamically discover and load all modules in this directory.
    
    Any .py file with a 'scan' function is considered a module.
    Modules can optionally define a 'META' dictionary for metadata.
    
    Returns:
        Dictionary mapping module names to their info
    """
    modules = {}
    package_dir = Path(__file__).parent
    
    # Iterate over all .py files in the directory
    for file_path in package_dir.glob("*.py"):
        module_name = file_path.stem
        
        if module_name.startswith('_') or module_name == 'base':
            continue
            
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(f"modules.{module_name}", file_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                # Check if it has a scan function (Required)
                if hasattr(mod, 'scan'):
                    
                    # Get Metadata (or default)
                    meta = getattr(mod, 'META', {
                        'description': f'{module_name} module',
                        'target_type': 'unknown',
                        'requirements': 'None'
                    })
                    
                    modules[module_name] = {
                        'description': meta.get('description'),
                        'target_type': meta.get('target_type'),
                        'requirements': meta.get('requirements'),
                        'available': True # If we imported it, it's available
                    }
                else:
                    # logger.debug(f"Skipping {module_name}: No scan() function found.")
                    pass
                    
        except Exception as e:
            logger.warning(f"Failed to load module {module_name}: {e}")
            modules[module_name] = {
                'description': 'Failed to load',
                'target_type': 'error',
                'requirements': 'Error',
                'available': False
            }
            
    return modules

__all__ = ['get_available_modules']
