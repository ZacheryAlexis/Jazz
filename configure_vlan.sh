#!/bin/bash

#############################################################################
# Jazz Lab 8 - VLAN Configuration Script
# This script will help you configure VLAN networking for your Jazz setup
#############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}   Jazz Lab 8 - VLAN Network Setup${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo

# Check sudo
if [ "$EUID" -ne 0 ]; then 
    log_error "This script requires sudo privileges"
    exec sudo "$0" "$@"
fi

# Show current network configuration
log_info "Current Network Configuration:"
echo
ip addr show | grep -E "^[0-9]+:|inet "
echo

# Get network interface
INTERFACES=$(ip -o link show | awk -F': ' '{print $2}' | grep -v '^lo$')
INTERFACE_COUNT=$(echo "$INTERFACES" | wc -l)

log_info "Available network interfaces:"
echo "$INTERFACES" | nl -v 1

if [ "$INTERFACE_COUNT" -eq 1 ]; then
    PRIMARY_IFACE=$(echo "$INTERFACES" | head -1)
    log_info "Auto-selected interface: $PRIMARY_IFACE"
else
    echo
    read -p "Enter the number of interface to use for VLAN: " IFACE_NUM
    PRIMARY_IFACE=$(echo "$INTERFACES" | sed -n "${IFACE_NUM}p")
fi

log_success "Selected interface: $PRIMARY_IFACE"
echo

# Get VLAN configuration
read -p "Enter VLAN ID (default: 10): " VLAN_ID
VLAN_ID=${VLAN_ID:-10}

read -p "Enter VLAN network (e.g., 192.168.10): " VLAN_NETWORK
if [ -z "$VLAN_NETWORK" ]; then
    log_error "VLAN network is required!"
    exit 1
fi

read -p "Enter this VM's last IP octet (e.g., 10 for $VLAN_NETWORK.10): " VM_OCTET
if [ -z "$VM_OCTET" ]; then
    log_error "IP octet is required!"
    exit 1
fi

VLAN_IP="$VLAN_NETWORK.$VM_OCTET"
VLAN_GATEWAY="$VLAN_NETWORK.1"

echo
log_info "VLAN Configuration Summary:"
echo "  Interface: $PRIMARY_IFACE"
echo "  VLAN ID: $VLAN_ID"
echo "  VLAN IP: $VLAN_IP/24"
echo "  Gateway: $VLAN_GATEWAY"
echo

read -p "Apply this configuration? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warning "Configuration cancelled"
    exit 0
fi

# Create netplan configuration
NETPLAN_FILE="/etc/netplan/60-jazz-vlan.yaml"

log_info "Creating netplan configuration..."

cat > "$NETPLAN_FILE" << NETPLAN_CONFIG
# Jazz Lab 8 VLAN Configuration
# Generated: $(date)
network:
  version: 2
  renderer: networkd
  
  ethernets:
    $PRIMARY_IFACE:
      dhcp4: true
      dhcp6: false
      
  vlans:
    vlan$VLAN_ID:
      id: $VLAN_ID
      link: $PRIMARY_IFACE
      addresses:
        - $VLAN_IP/24
      routes:
        - to: $VLAN_NETWORK.0/24
          via: $VLAN_GATEWAY
          metric: 100
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
NETPLAN_CONFIG

log_success "Netplan config created: $NETPLAN_FILE"

# Apply configuration
log_info "Applying netplan configuration..."
netplan apply

sleep 2

# Verify VLAN interface
if ip addr show "vlan$VLAN_ID" &> /dev/null; then
    ASSIGNED_IP=$(ip addr show "vlan$VLAN_ID" | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
    log_success "VLAN interface created successfully!"
    log_success "VLAN IP assigned: $ASSIGNED_IP"
else
    log_error "VLAN interface creation failed"
    exit 1
fi

# Update firewall for VLAN subnet
log_info "Updating firewall rules for VLAN..."
ufw allow from "$VLAN_NETWORK.0/24"
ufw allow to "$VLAN_NETWORK.0/24"
log_success "Firewall updated"

# Update backend .env if it exists
if [ -f "/home/$(logname)/Jazz/backend/.env" ]; then
    log_info "Updating backend configuration..."
    if ! grep -q "VLAN_IP" "/home/$(logname)/Jazz/backend/.env"; then
        echo "VLAN_IP=$VLAN_IP" >> "/home/$(logname)/Jazz/backend/.env"
        echo "VLAN_NETWORK=$VLAN_NETWORK.0/24" >> "/home/$(logname)/Jazz/backend/.env"
    fi
    log_success "Backend configured"
fi

echo
log_success "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_success "   VLAN Configuration Complete! 🎉"
log_success "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "VLAN Details:"
echo "  • Interface: vlan$VLAN_ID"
echo "  • IP Address: $VLAN_IP/24"
echo "  • Network: $VLAN_NETWORK.0/24"
echo "  • Gateway: $VLAN_GATEWAY"
echo
echo "Next Steps:"
echo "  1. Configure other VMs in the same VLAN"
echo "  2. Use the discover_vms.sh script to find other Jazz instances"
echo "  3. Test connectivity: ping <other-vm-ip>"
echo
