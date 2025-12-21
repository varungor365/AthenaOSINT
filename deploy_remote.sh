#!/bin/bash
# Quick deployment command for 16GB droplet

echo "🚀 Deploying AthenaOSINT v3.0 with 16GB optimizations..."

# SSH to droplet and execute
ssh root@143.110.254.40 << 'ENDSSH'
cd /root/AthenaOSINT
git pull origin main
chmod +x scripts/deploy_16gb.sh
./scripts/deploy_16gb.sh
ENDSSH

echo "✅ Deployment complete!"
echo "Access dashboard: http://143.110.254.40"
