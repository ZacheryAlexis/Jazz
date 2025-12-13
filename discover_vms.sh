#!/bin/bash

#############################################################################
# Jazz VM Discovery Script
# Scans the VLAN network for other Jazz instances
#############################################################################

VLAN_NETWORK="${1:-192.168.10}"

if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo "Usage: $0 [network]"
    echo "Example: $0 192.168.10"
    echo "Default network: 192.168.10"
    exit 0
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Jazz VM Discovery"
echo "  Scanning: $VLAN_NETWORK.0/24"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

FOUND=0

for i in {1..254}; do
    IP="$VLAN_NETWORK.$i"
    
    # Quick ping check (timeout 1 second)
    if timeout 0.5 ping -c 1 "$IP" &> /dev/null; then
        echo "✓ Found VM at $IP"
        FOUND=$((FOUND + 1))
        
        # Check for Jazz Backend
        if timeout 2 curl -s "http://$IP:3000/api/health" &> /dev/null 2>&1; then
            echo "  └─ 🎵 Running Jazz Backend (port 3000)"
        fi
        
        # Check for Jazz Frontend
        if timeout 2 curl -s "http://$IP:4200" &> /dev/null 2>&1; then
            echo "  └─ 🖥️  Running Jazz Frontend (port 4200)"
        fi
        
        # Check SSH
        if timeout 1 nc -z "$IP" 22 &> /dev/null; then
            echo "  └─ 🔐 SSH available (port 22)"
        fi
        
        echo
    fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Scan complete! Found $FOUND active host(s)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
