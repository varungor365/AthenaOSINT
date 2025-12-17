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
    package_dir = Path(__file__).parent
    
    # Import centralized registry
    from modules.registry import MODULE_REGISTRY
    
    # 1. Start with the Registry as the base
    modules = MODULE_REGISTRY.copy()
    
    # 2. Check which files actually exist
    # Get all .py files
    existing_files = {f.stem for f in package_dir.glob("*.py") if f.stem != 'registry' and not f.stem.startswith('_')}

    # 3. Update status
    for mod_name, meta in modules.items():
        if mod_name in existing_files:
            meta['available'] = True
        else:
            meta['available'] = False
            # Optional: We could hide missing modules, but showing them as disabled might be better?
            # For now, let's keep them but maybe the UI handles them.
            # Actually, the UI iterates all of them.
            
    # 4. Add any files found that are NOT in registry? (Optional, skipping for now to enforce registry usage)
            
    return modules

__all__ = ['get_available_modules']
