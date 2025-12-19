#!/bin/bash
echo "[*] Updating AthenaOSINT Stack..."
# Pull latest images if we were using remote ones (we are building local mostly)
# docker-compose pull

echo "[*] Restarting Services with OpenBullet2..."
docker-compose up -d --remove-orphans

echo "[*] Waiting for services to initialize..."
sleep 5

echo "[*] Status Check:"
docker-compose ps

echo ""
echo "[SUCCESS] OpenBullet2 should now be running on port 8069."
echo "Access the Dashboard at: http://localhost:5000/openbullet"
echo "Access Native Interface at: http://localhost:8069"
