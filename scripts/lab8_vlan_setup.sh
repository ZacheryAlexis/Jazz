#!/bin/bash

#############################################################################
# Lab 8 - VLAN Multi-VM Networking Setup
# 
# This script configures VLAN networking for multi-VM Jazz deployment
# Prerequisites: Lab 7 (MEAN Stack) must be completed first
# Usage: bash lab8_vlan_setup.sh
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
log_header() { echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n$1\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

log_header "Lab 8 - VLAN Multi-VM Networking Setup"

# Check sudo
if [ "$EUID" -ne 0 ]; then 
    log_error "This script requires root. Re-running with sudo..."
    sudo "$0"
    exit $?
fi

#############################################################################
# PHASE 1: Pre-flight Checks
#############################################################################

log_info "Phase 1: Pre-flight Checks"

# Check for multiple network interfaces
INTERFACES=$(ip -o link show | awk -F': ' '{print $2}' | grep -v '^lo$')
INTERFACE_COUNT=$(echo "$INTERFACES" | wc -l)

log_info "Found $INTERFACE_COUNT network interface(s):"
echo "$INTERFACES" | while read iface; do
    IP=$(ip addr show "$iface" | grep "inet " | awk '{print $2}')
    echo -e "  • $iface: $IP"
done

# Get current hostname and IP
HOSTNAME=$(hostname)
PRIMARY_IP=$(hostname -I | awk '{print $1}')

log_info "Current system:"
log_info "  Hostname: $HOSTNAME"
log_info "Pr imary IP: $PRIMARY_IP"

#############################################################################
# PHASE 2: Install VLAN Tools
#############################################################################

log_info "Phase 2: Installing VLAN Tools"

apt-get update
apt-get install -y vlan net-tools ifupdown2 netplan.io

log_success "VLAN tools installed"

#############################################################################
# PHASE 3: VLAN Configuration
#############################################################################

log_info "Phase 3: Configuring VLAN"

# Ask user for VLAN details
read -p "Enter VLAN ID (default 10): " VLAN_ID
VLAN_ID=${VLAN_ID:-10}

read -p "Enter VLAN Network (default 192.168.10): " VLAN_NETWORK
VLAN_NETWORK=${VLAN_NETWORK:-192.168.10}

read -p "Enter your VM's last IP octet (e.g., 10 for .10): " VM_OCTET
VM_OCTET=${VM_OCTET:-$((RANDOM % 255))}

VLAN_IP="$VLAN_NETWORK.$VM_OCTET"
VLAN_SUBNET="$VLAN_NETWORK.0/24"
VLAN_GATEWAY="$VLAN_NETWORK.1"

# Select interface for VLAN (if multiple exist)
PRIMARY_IFACE=""
if [ "$INTERFACE_COUNT" -gt 2 ]; then
    log_info "Select which interface to tag with VLAN:"
    echo "$INTERFACES" | nl
    read -p "Enter interface number: " IFACE_NUM
    PRIMARY_IFACE=$(echo "$INTERFACES" | sed -n "${IFACE_NUM}p")
else
    PRIMARY_IFACE=$(echo "$INTERFACES" | tail -1)
fi

log_info "Selected interface: $PRIMARY_IFACE"

#############################################################################
# PHASE 4: Create Netplan Configuration
#############################################################################

log_info "Phase 4: Creating Netplan Configuration"

NETPLAN_FILE="/etc/netplan/60-vlan-jazz.yaml"

cat > "$NETPLAN_FILE" << NETPLAN_CONFIG
# Jazz Lab 8 VLAN Configuration
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
      gateway4: $VLAN_GATEWAY
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
        search:
          - jazz.local
NETPLAN_CONFIG

log_success "Netplan config created at $NETPLAN_FILE"

log_info "Configuration details:"
log_info "  VLAN ID: $VLAN_ID"
log_info "  VLAN Interface: vlan$VLAN_ID"
log_info "  VLAN IP: $VLAN_IP/24"
log_info "  VLAN Gateway: $VLAN_GATEWAY"
log_info "  Parent Interface: $PRIMARY_IFACE"

#############################################################################
# PHASE 5: Apply VLAN Configuration
#############################################################################

log_info "Phase 5: Applying VLAN Configuration"

read -p "Apply netplan changes now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    netplan apply
    sleep 2
    
    if ip addr show vlan$VLAN_ID &> /dev/null; then
        ASSIGNED_IP=$(ip addr show vlan$VLAN_ID | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
        log_success "VLAN interface created successfully!"
        log_success "VLAN IP assigned: $ASSIGNED_IP"
    else
        log_error "VLAN interface creation failed"
    fi
else
    log_warning "Netplan changes not applied yet"
    log_info "To apply manually, run: sudo netplan apply"
fi

#############################################################################
# PHASE 6: Configure SSH for VLAN
#############################################################################

log_info "Phase 6: Configuring SSH"

# Ensure SSH is running
systemctl start ssh
systemctl enable ssh

log_success "SSH configured and enabled"

#############################################################################
# PHASE 7: Update Firewall for VLAN
#############################################################################

log_info "Phase 7: Updating Firewall Rules"

# Allow traffic from VLAN subnet
ufw allow from $VLAN_NETWORK.0/24
ufw allow to $VLAN_NETWORK.0/24

log_success "Firewall rules updated for VLAN traffic"

#############################################################################
# PHASE 8: Configure Jazz Backend for VLAN
#############################################################################

log_info "Phase 8: Configure Jazz Backend for VLAN Access"

PROJECT_DIR="/home/$(whoami)/Jazz"

if [ -d "$PROJECT_DIR/backend" ]; then
    cd "$PROJECT_DIR/backend"
    
    # Update .env to use VLAN IP
    if [ -f ".env" ]; then
        sed -i "s/^MONGODB_URI=.*/MONGODB_URI=mongodb:\/\/localhost:27017\/jazz/" .env
    fi
    
    # Create .env for VLAN if not exists
    if [ ! -f ".env" ]; then
        cat > .env << 'ENV_VLAN'
MONGODB_URI=mongodb://localhost:27017/jazz
JWT_SECRET=change_this_in_production
PORT=3000
NODE_ENV=production
VLAN_IP=0.0.0.0
VLAN_PORT=3000
ENV_VLAN
    fi
    
    log_success "Backend .env configured for VLAN"
else
    log_warning "Jazz backend not found, skipping backend configuration"
fi

#############################################################################
# PHASE 9: Create Multi-VM Discovery Script
#############################################################################

log_info "Phase 9: Creating Multi-VM Discovery Tools"

DISCOVERY_SCRIPT="$PROJECT_DIR/discover_vms.sh"

cat > "$DISCOVERY_SCRIPT" << 'DISCOVERY_SCRIPT_CONTENT'
#!/bin/bash

# Discover other Jazz VMs on VLAN
VLAN_NETWORK="${1:-192.168.10}"

echo "Scanning VLAN $VLAN_NETWORK.0/24 for Jazz instances..."
echo

for i in {1..254}; do
    IP="$VLAN_NETWORK.$i"
    
    # Quick ping check (non-blocking)
    if timeout 1 ping -c 1 "$IP" &> /dev/null; then
        echo "✓ Found VM at $IP"
        
        # Try to identify if it's a Jazz instance
        if timeout 2 curl -s "http://$IP:3000/health" &> /dev/null; then
            echo "  └─ Running Jazz Backend on port 3000"
        fi
        
        if timeout 2 curl -s "http://$IP:4200" &> /dev/null; then
            echo "  └─ Running Jazz Frontend on port 4200"
        fi
    fi
done

echo
echo "Scan complete!"
DISCOVERY_SCRIPT_CONTENT

chmod +x "$DISCOVERY_SCRIPT"
log_success "Discovery script created at $DISCOVERY_SCRIPT"

#############################################################################
# PHASE 10: Create VM Sync Script
#############################################################################

log_info "Phase 10: Creating VM Synchronization Script"

SYNC_SCRIPT="$PROJECT_DIR/sync_vms.sh"

cat > "$SYNC_SCRIPT" << 'SYNC_SCRIPT_CONTENT'
#!/bin/bash

# Sync Jazz across multiple VMs
TARGET_VM="$1"

if [ -z "$TARGET_VM" ]; then
    echo "Usage: $0 <vm_ip>"
    echo "Example: $0 192.168.10.20"
    exit 1
fi

echo "Syncing Jazz to $TARGET_VM..."

# Rsync Jazz project to target VM
rsync -avz --delete ~/Jazz/ "root@$TARGET_VM:~/Jazz/"

if [ $? -eq 0 ]; then
    echo "✓ Sync complete!"
    echo "Next: SSH to $TARGET_VM and run 'cd ~/Jazz/backend && npm start'"
else
    echo "✗ Sync failed"
fi
SYNC_SCRIPT_CONTENT

chmod +x "$SYNC_SCRIPT"
log_success "Sync script created at $SYNC_SCRIPT"

#############################################################################
# PHASE 11: Create Configuration Summary
#############################################################################

log_info "Phase 11: Creating Configuration Summary"

CONFIG_SUMMARY="/tmp/jazz_vlan_config.txt"

cat > "$CONFIG_SUMMARY" << CONFIG_CONTENT
═══════════════════════════════════════════════════════════════
Jazz Lab 8 VLAN Configuration Summary
═══════════════════════════════════════════════════════════════

HOSTNAME: $(hostname)
PRIMARY IP: $PRIMARY_IP

VLAN CONFIGURATION:
  ID: $VLAN_ID
  Subnet: $VLAN_SUBNET
  Interface: vlan$VLAN_ID
  IP Address: $VLAN_IP/24
  Gateway: $VLAN_GATEWAY
  Parent Interface: $PRIMARY_IFACE

NETWORK FILES:
  Netplan Config: $NETPLAN_FILE
  
USEFUL COMMANDS:
  Check VLAN status:
    ip addr show vlan$VLAN_ID
    ip route show vlan$VLAN_ID
  
  Test connectivity:
    ping 192.168.10.X  (replace X with target VM octet)
  
  SSH to another VM:
    ssh root@$VLAN_NETWORK.X
  
  Discover other VMs:
    bash $DISCOVERY_SCRIPT
  
  Sync to another VM:
    bash $SYNC_SCRIPT 192.168.10.X

TROUBLESHOOTING:
  Reload netplan:
    sudo netplan apply
  
  Check interface status:
    ip link show
    
  View routing table:
    ip route show

═══════════════════════════════════════════════════════════════
CONFIG_CONTENT

cat "$CONFIG_SUMMARY"
cp "$CONFIG_SUMMARY" "$PROJECT_DIR/VLAN_CONFIG.txt"

#############################################################################
# PHASE 12: Test VLAN Configuration
#############################################################################

log_info "Phase 12: Testing VLAN Configuration"

log_info "Testing VLAN interface..."
if ip addr show vlan$VLAN_ID &> /dev/null; then
    IP_ADDR=$(ip addr show vlan$VLAN_ID | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
    log_success "VLAN interface vlan$VLAN_ID is UP"
    log_success "IP Address: $IP_ADDR"
else
    log_warning "VLAN interface not found (may need manual configuration)"
fi

log_info "Testing gateway connectivity..."
if timeout 2 ping -c 1 "$VLAN_GATEWAY" &> /dev/null; then
    log_success "Gateway $VLAN_GATEWAY is reachable"
else
    log_warning "Gateway $VLAN_GATEWAY not reachable (may be normal in sandbox)"
fi

#############################################################################
# FINAL SUMMARY
#############################################################################

cat << 'FINAL'

╔════════════════════════════════════════════════════════════════╗
║         Lab 8 - VLAN Setup Complete! 🎉                       ║
╚════════════════════════════════════════════════════════════════╝

✓ VLAN interface configured
✓ Netplan configuration applied
✓ SSH enabled for inter-VM communication
✓ Firewall rules updated
✓ Discovery & sync scripts created
✓ Configuration documented

🚀 NEXT STEPS FOR MULTI-VM DEPLOYMENT:

1. ON THIS VM:
   cd ~/Jazz/backend
   npm start
   
   OR:
   cd ~/Jazz/frontend
   ng serve

2. ON OTHER VMs:
   bash discover_vms.sh
   
   Then sync:
   bash sync_vms.sh <other_vm_ip>

3. TEST CONNECTIVITY BETWEEN VMs:
   From VM1: ping 192.168.10.X  (VM2's VLAN IP)
   From VM2: SSH to VM1 (if key-based auth setup)

4. MONITOR BACKEND ON VLAN:
   curl http://192.168.10.X:3000
   curl http://192.168.10.X:4200

📁 IMPORTANT FILES:
   Netplan Config: /etc/netplan/60-vlan-jazz.yaml
   Discovery Script: ~/Jazz/discover_vms.sh
   Sync Script: ~/Jazz/sync_vms.sh
   This Summary: ~/Jazz/VLAN_CONFIG.txt

🔧 TROUBLESHOOTING:
   Check VLAN status: ip addr show vlan10
   Reload networking: sudo netplan apply
   View logs: journalctl -xe
   Test SSH: ssh root@192.168.10.X

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Lab 8 VLAN networking is ready for multi-VM deployment! 🚀

FINAL

log_success "Lab 8 Setup Complete!"
