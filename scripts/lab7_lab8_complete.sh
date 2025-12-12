#!/bin/bash

#############################################################################
# Jazz IT 340 - Lab 7 & Lab 8 Complete Automation Script
# 
# This script automates the complete setup for Lab 7 (MEAN Stack) and 
# Lab 8 (Multi-VM VLAN networking) on Ubuntu/Debian systems
#
# Usage: bash lab7_lab8_complete.sh
#############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

#############################################################################
# PHASE 0: Pre-flight Checks
#############################################################################

log_info "Starting Jazz Lab 7 & Lab 8 Complete Setup..."
log_info "================================================"

# Check if running as root (needed for system packages)
if [ "$EUID" -ne 0 ]; then 
    log_warning "This script needs sudo for system package installation"
    log_info "Re-running with sudo..."
    sudo "$0"
    exit $?
fi

log_success "Running as root"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    log_error "Cannot detect OS. Please run on Ubuntu/Debian"
    exit 1
fi

log_info "Detected OS: $OS"

#############################################################################
# PHASE 1: System Updates & Prerequisites
#############################################################################

log_info "Phase 1: System Updates & Prerequisites"
log_info "========================================"

apt-get update
apt-get upgrade -y

# Install essential tools
log_info "Installing essential tools..."
apt-get install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    net-tools \
    ufw \
    openssh-server \
    openssh-client \
    build-essential \
    python3 \
    python3-pip \
    python3-venv

log_success "Essential tools installed"

#############################################################################
# PHASE 2: Node.js & npm Installation
#############################################################################

log_info "Phase 2: Node.js & npm Installation"
log_info "======================================"

if command -v node &> /dev/null; then
    log_warning "Node.js already installed: $(node -v)"
else
    log_info "Installing Node.js 18 LTS..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    apt-get install -y nodejs
    log_success "Node.js installed: $(node -v)"
fi

if command -v npm &> /dev/null; then
    log_success "npm already installed: $(npm -v)"
else
    log_error "npm installation failed"
    exit 1
fi

# Install Angular CLI globally
npm install -g @angular/cli
log_success "Angular CLI installed"

#############################################################################
# PHASE 3: MongoDB Installation
#############################################################################

log_info "Phase 3: MongoDB Installation"
log_info "=============================="

if command -v mongod &> /dev/null; then
    log_warning "MongoDB already installed"
else
    log_info "Installing MongoDB..."
    apt-get install -y mongodb
    
    # Start and enable MongoDB
    systemctl start mongodb
    systemctl enable mongodb
    log_success "MongoDB installed and started"
fi

# Verify MongoDB
if mongo --version &> /dev/null; then
    log_success "MongoDB verified: $(mongod --version | head -1)"
else
    log_warning "MongoDB client verification failed, but server may still work"
fi

#############################################################################
# PHASE 4: Clone/Setup Jazz Project
#############################################################################

log_info "Phase 4: Clone/Setup Jazz Project"
log_info "=================================="

PROJECT_DIR="/home/$(whoami)/Jazz"

if [ -d "$PROJECT_DIR" ]; then
    log_warning "Jazz directory already exists at $PROJECT_DIR"
    read -p "Update from git? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PROJECT_DIR"
        git pull origin main
        log_success "Jazz updated"
    fi
else
    log_info "Cloning Jazz repository..."
    mkdir -p /home/$(whoami)
    cd /home/$(whoami)
    git clone https://github.com/ZacheryAlexis/Jazz.git
    log_success "Jazz cloned to $PROJECT_DIR"
fi

#############################################################################
# PHASE 5: Backend Setup (Lab 7)
#############################################################################

log_info "Phase 5: Backend Setup (Lab 7)"
log_info "==============================="

BACKEND_DIR="$PROJECT_DIR/backend"

if [ ! -d "$BACKEND_DIR" ]; then
    log_info "Creating backend directory..."
    mkdir -p "$BACKEND_DIR"
fi

# Copy backend template files
log_info "Setting up backend from templates..."
cp "$PROJECT_DIR/templates/backend/server.js" "$BACKEND_DIR/"
cp "$PROJECT_DIR/templates/backend/package.json" "$BACKEND_DIR/"

cd "$BACKEND_DIR"

# Create .env file
log_info "Creating .env file..."
cat > .env << 'EOF'
MONGODB_URI=mongodb://localhost:27017/jazz
JWT_SECRET=your_super_secret_key_change_this_in_production_12345
PORT=3000
NODE_ENV=production
EOF

log_warning "⚠️  Update JWT_SECRET in $BACKEND_DIR/.env for production!"

# Install dependencies
log_info "Installing backend dependencies..."
npm install

log_success "Backend setup complete"

#############################################################################
# PHASE 6: Frontend Setup (Lab 7)
#############################################################################

log_info "Phase 6: Frontend Setup (Lab 7)"
log_info "==============================="

FRONTEND_DIR="$PROJECT_DIR/frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
    log_info "Creating Angular frontend project..."
    cd /tmp
    ng new Jazz-Frontend --routing --skip-git
    mv Jazz-Frontend "$PROJECT_DIR/frontend"
else
    log_warning "Frontend directory already exists"
fi

cd "$FRONTEND_DIR"

# Install dependencies
log_info "Installing frontend dependencies..."
npm install

# Create component directories
log_info "Creating components..."
ng generate component components/login --skip-tests
ng generate component components/chat --skip-tests
ng generate service services/auth --skip-tests

# Copy component files
log_info "Copying component files from templates..."
cp "$PROJECT_DIR/templates/frontend/login.component.ts" src/app/components/login/
cp "$PROJECT_DIR/templates/frontend/login.component.html" src/app/components/login/
cp "$PROJECT_DIR/templates/frontend/login.component.css" src/app/components/login/

cp "$PROJECT_DIR/templates/frontend/chat.component.ts" src/app/components/chat/
cp "$PROJECT_DIR/templates/frontend/chat.component.html" src/app/components/chat/
cp "$PROJECT_DIR/templates/frontend/chat.component.css" src/app/components/chat/

# Setup routing
log_info "Configuring routing..."
cat > src/app/app-routing.module.ts << 'EOF'
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { ChatComponent } from './components/chat/chat.component';

const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'chat', component: ChatComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
EOF

# Update app.module.ts
log_info "Updating AppModule..."
cat > src/app/app.module.ts << 'EOF'
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { LoginComponent } from './components/login/login.component';
import { ChatComponent } from './components/chat/chat.component';

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    ChatComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
EOF

log_success "Frontend setup complete"

#############################################################################
# PHASE 7: Environment Configuration
#############################################################################

log_info "Phase 7: Environment Configuration"
log_info "===================================="

# Create .gitignore
log_info "Creating .gitignore..."
cat > "$PROJECT_DIR/.gitignore" << 'EOF'
node_modules/
.env
dist/
__pycache__/
.angular/
*.log
.DS_Store
.vscode/
.idea/
*.swp
*.swo
*~
EOF

# Create startup scripts
log_info "Creating startup scripts..."

# Backend startup script
cat > "$BACKEND_DIR/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
npm start
EOF
chmod +x "$BACKEND_DIR/start.sh"

# Frontend startup script
cat > "$FRONTEND_DIR/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
ng serve
EOF
chmod +x "$FRONTEND_DIR/start.sh"

log_success "Startup scripts created"

#############################################################################
# PHASE 8: Lab 8 - Multi-VM VLAN Configuration
#############################################################################

log_info "Phase 8: Lab 8 - VLAN Configuration"
log_info "====================================="

# Get network info for VLAN setup
HOSTNAME=$(hostname)
IP_ADDR=$(hostname -I | awk '{print $1}')

log_info "Current hostname: $HOSTNAME"
log_info "Current IP: $IP_ADDR"

# Create VLAN configuration script
log_info "Creating VLAN configuration script..."
cat > "$PROJECT_DIR/setup_vlan.sh" << 'EOF'
#!/bin/bash

# VLAN Configuration Script for Lab 8
# This script configures a secondary network interface for VLAN 10

VLAN_ID=10
VLAN_IP="192.168.10.$(hostname -I | cut -d'.' -f4)"  # Auto-assign from last octet
VLAN_NETMASK="255.255.255.0"
VLAN_GATEWAY="192.168.10.1"

INTERFACE="eth1"  # Adjust if your secondary interface has different name

log_info "Configuring VLAN $VLAN_ID..."
log_info "Interface: $INTERFACE"
log_info "VLAN IP: $VLAN_IP"

# Create netplan configuration
sudo tee /etc/netplan/60-vlan.yaml > /dev/null << NETPLAN
network:
  version: 2
  ethernets:
    $INTERFACE:
      dhcp4: false
      dhcp6: false
  vlans:
    vlan$VLAN_ID:
      id: $VLAN_ID
      link: $INTERFACE
      addresses: [$VLAN_IP/$VLAN_NETMASK]
      gateway4: $VLAN_GATEWAY
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
NETPLAN

log_info "Applying netplan configuration..."
sudo netplan apply

log_success "VLAN $VLAN_ID configured!"
log_info "New VLAN IP: $VLAN_IP"
EOF

chmod +x "$PROJECT_DIR/setup_vlan.sh"

log_warning "To configure VLAN, run: $PROJECT_DIR/setup_vlan.sh"
log_warning "You may need to adjust VLAN_ID and INTERFACE variables"

#############################################################################
# PHASE 9: Firewall Configuration (UFW)
#############################################################################

log_info "Phase 9: Firewall Configuration"
log_info "================================"

# Enable UFW
ufw --force enable

# Allow SSH
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow Node backend
ufw allow 3000/tcp

# Allow Angular dev server
ufw allow 4200/tcp

# Allow MongoDB (only from localhost by default)
ufw allow from 127.0.0.1 to 127.0.0.1 port 27017

log_success "Firewall configured"
log_info "Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 3000 (Backend), 4200 (Frontend)"

#############################################################################
# PHASE 10: Service Configuration
#############################################################################

log_info "Phase 10: Service Configuration"
log_info "================================"

# Create systemd service for backend
log_info "Creating backend service..."
sudo tee /etc/systemd/system/jazz-backend.service > /dev/null << 'SERVICE'
[Unit]
Description=Jazz Backend Service
After=network.target mongodb.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/jazz/backend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# Create systemd service for frontend build
log_info "Creating frontend service..."
sudo tee /etc/systemd/system/jazz-frontend.service > /dev/null << 'SERVICE'
[Unit]
Description=Jazz Frontend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/jazz/frontend
ExecStart=/usr/bin/ng serve --host 0.0.0.0
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload

log_success "Services created (not started yet)"
log_info "To start backend: sudo systemctl start jazz-backend"
log_info "To start frontend: sudo systemctl start jazz-frontend"

#############################################################################
# PHASE 11: Testing
#############################################################################

log_info "Phase 11: Testing Setup"
log_info "======================="

# Test Node
log_info "Testing Node.js..."
node -v
npm -v

# Test MongoDB
log_info "Testing MongoDB..."
systemctl status mongodb --no-pager | head -3

# Test Angular
log_info "Testing Angular CLI..."
ng version | head -3

log_success "All tools verified"

#############################################################################
# PHASE 12: Final Summary
#############################################################################

log_info "Phase 12: Setup Complete!"
log_info "=========================="

cat << 'EOF'

╔════════════════════════════════════════════════════════════════╗
║          Jazz Lab 7 & Lab 8 Setup Complete! 🎉                ║
╚════════════════════════════════════════════════════════════════╝

📊 SETUP SUMMARY:
─────────────────
✓ System packages installed
✓ Node.js & npm installed
✓ MongoDB installed & running
✓ Angular CLI installed
✓ Jazz project cloned
✓ Backend configured (Lab 7)
✓ Frontend configured (Lab 7)
✓ VLAN setup script created (Lab 8)
✓ Firewall configured
✓ Systemd services created

🚀 NEXT STEPS:
─────────────

1. UPDATE ENVIRONMENT VARIABLES:
   Edit the .env file with secure values:
   
   sudo nano /home/$(whoami)/Jazz/backend/.env
   
   Change JWT_SECRET to a secure random value

2. START SERVICES:
   
   # Option A: Manual (for testing)
   cd /home/$(whoami)/Jazz/backend
   npm start
   
   cd /home/$(whoami)/Jazz/frontend
   ng serve
   
   # Option B: Systemd (for production)
   sudo systemctl start jazz-backend
   sudo systemctl start jazz-frontend
   sudo systemctl enable jazz-backend
   sudo systemctl enable jazz-frontend

3. TEST THE APPLICATION:
   
   Backend: curl http://localhost:3000
   Frontend: Open browser to http://localhost:4200
   MongoDB: mongo --eval "db.adminCommand('ping')"

4. CONFIGURE VLAN (Lab 8):
   
   ./setup_vlan.sh
   
   Then update /etc/netplan/60-vlan.yaml as needed

5. VIEW LOGS:
   
   # Backend logs
   sudo journalctl -u jazz-backend -f
   
   # Frontend logs
   sudo journalctl -u jazz-frontend -f

📁 IMPORTANT PATHS:
──────────────────
Project:    /home/$(whoami)/Jazz
Backend:    /home/$(whoami)/Jazz/backend
Frontend:   /home/$(whoami)/Jazz/frontend
Config:     /home/$(whoami)/Jazz/backend/.env
VLAN Setup: /home/$(whoami)/Jazz/setup_vlan.sh

🔒 SECURITY NOTES:
─────────────────
• Change JWT_SECRET in .env immediately!
• Use HTTPS in production
• Secure MongoDB with authentication
• Restrict firewall to only needed ports
• Use SSH keys instead of passwords

❓ TROUBLESHOOTING:
──────────────────
If something fails, check logs:
  sudo journalctl -xe
  
For MongoDB issues:
  sudo systemctl status mongodb
  mongo --eval "db.adminCommand('ping')"

For Node issues:
  npm install  (in backend directory)
  npm audit fix

For Angular issues:
  npm cache clean --force
  npm install

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ready to proceed? Let's go! 🚀

EOF

log_success "Lab 7 & Lab 8 Setup Complete!"
