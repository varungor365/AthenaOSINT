#!/bin/bash
# Debug script to find the web service issue

echo "=== Testing Python imports ==="
cd /root/AthenaOSINT
/root/AthenaOSINT/venv/bin/python3 /tmp/test_import.py

echo ""
echo "=== Checking if mrholmes routes exist in code ==="
grep -n "def mrholmes_dashboard" web/routes.py

echo ""
echo "=== Testing direct Flask app creation ==="
timeout 5 /root/AthenaOSINT/venv/bin/python3 -c "
import sys
sys.path.insert(0, '/root/AthenaOSINT')
try:
    from web import create_app
    app, socketio = create_app()
    print('App created successfully')
    print(f'Registered routes: {[str(r) for r in app.url_map.iter_rules() if \"mrholmes\" in str(r)]}')
except Exception as e:
    print(f'Error creating app: {e}')
    import traceback
    traceback.print_exc()
" 2>&1

echo ""
echo "=== Checking web service status ==="
systemctl status athena-web --no-pager | head -15

echo ""
echo "Done!"
