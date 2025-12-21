#!/usr/bin/env python3
"""Test imports to find the issue"""

print("Testing imports...")

try:
    print("1. Importing web...")
    from web import create_app
    print("   ✓ web import OK")
except Exception as e:
    print(f"   ✗ web import FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    print("2. Importing web.routes...")
    from web import routes
    print("   ✓ web.routes import OK")
except Exception as e:
    print(f"   ✗ web.routes import FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    print("3. Importing modules.mrholmes...")
    from modules.mrholmes import MrHolmes
    print("   ✓ modules.mrholmes import OK")
except Exception as e:
    print(f"   ✗ modules.mrholmes import FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nAll tests complete.")
