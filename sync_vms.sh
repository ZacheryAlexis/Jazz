#!/bin/bash

#############################################################################
# Jazz VM Sync Script
# Synchronize Jazz project to other VMs via rsync
#############################################################################

TARGET_VM="$1"
TARGET_USER="${2:-zach}"

if [ -z "$TARGET_VM" ]; then
    echo "Usage: $0 <target_vm_ip> [username]"
    echo "Example: $0 192.168.10.20 zach"
    echo ""
    echo "This script uses rsync to sync the Jazz project to another VM"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Jazz VM Sync"
echo "  Target: $TARGET_USER@$TARGET_VM"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Check if target is reachable
if ! ping -c 1 -W 2 "$TARGET_VM" &> /dev/null; then
    echo "✗ Error: Cannot reach $TARGET_VM"
    exit 1
fi

echo "✓ Target VM is reachable"

# Sync Jazz project (excluding node_modules, .git, etc.)
echo "Syncing Jazz project..."
echo

rsync -avz --progress \
    --exclude 'node_modules' \
    --exclude '.git' \
    --exclude '.angular' \
    --exclude 'dist' \
    --exclude '.env' \
    --exclude '*.log' \
    ~/Jazz/ "$TARGET_USER@$TARGET_VM:~/Jazz/"

if [ $? -eq 0 ]; then
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✓ Sync complete!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    echo "Next steps on $TARGET_VM:"
    echo "  1. SSH to target: ssh $TARGET_USER@$TARGET_VM"
    echo "  2. Install dependencies:"
    echo "     cd ~/Jazz/backend && npm install"
    echo "     cd ~/Jazz/frontend && npm install"
    echo "  3. Configure .env file in backend/"
    echo "  4. Start services:"
    echo "     cd ~/Jazz/backend && ./start.sh"
    echo "     cd ~/Jazz/frontend && ./start.sh"
else
    echo "✗ Sync failed"
    exit 1
fi
