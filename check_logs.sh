#!/bin/bash
# Check service logs for errors

echo "Checking recent service logs..."
sudo journalctl -u athena.service -n 50 --no-pager
