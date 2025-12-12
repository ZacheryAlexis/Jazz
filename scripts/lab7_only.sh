#!/bin/bash

#############################################################################
# Lab 7 Only - MEAN Stack Setup (Backend + Frontend)
# 
# Run this if you just want to set up the MEAN stack without VLAN
# Usage: bash lab7_only.sh
#############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

log_info "Starting Lab 7 - MEAN Stack Setup"
log_info "==================================="

# Check sudo
if [ "$EUID" -ne 0 ]; then 
    sudo "$0"
    exit $?
fi

#############################################################################
# PHASE 1: Quick System Setup
#############################################################################

log_info "Phase 1: Installing System Dependencies"
apt-get update
apt-get install -y curl wget git build-essential python3 python3-pip

#############################################################################
# PHASE 2: Node.js
#############################################################################

log_info "Phase 2: Installing Node.js 18 LTS"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    apt-get install -y nodejs
fi
log_success "Node.js: $(node -v), npm: $(npm -v)"

#############################################################################
# PHASE 3: MongoDB
#############################################################################

log_info "Phase 3: Installing MongoDB"
if ! command -v mongod &> /dev/null; then
    apt-get install -y mongodb
    systemctl start mongodb
    systemctl enable mongodb
fi
log_success "MongoDB installed and running"

#############################################################################
# PHASE 4: Angular CLI
#############################################################################

log_info "Phase 4: Installing Angular CLI"
npm install -g @angular/cli
log_success "Angular CLI installed"

#############################################################################
# PHASE 5: Project Setup
#############################################################################

log_info "Phase 5: Setting up Jazz project"

PROJECT_DIR="/home/$(whoami)/Jazz"

if [ ! -d "$PROJECT_DIR" ]; then
    cd /home/$(whoami)
    git clone https://github.com/ZacheryAlexis/Jazz.git
fi

cd "$PROJECT_DIR"

# Backend setup
log_info "Configuring Backend..."
mkdir -p backend
cp templates/backend/server.js backend/
cp templates/backend/package.json backend/

cd backend
cat > .env << 'EOF'
MONGODB_URI=mongodb://localhost:27017/jazz
JWT_SECRET=lab7_default_secret_change_in_production
PORT=3000
EOF

npm install
log_success "Backend ready"

# Frontend setup
log_info "Configuring Frontend..."
cd "$PROJECT_DIR"

if [ ! -d "frontend" ]; then
    cd /tmp
    ng new Jazz-Frontend --routing --skip-git
    mv Jazz-Frontend "$PROJECT_DIR/frontend"
fi

cd "$PROJECT_DIR/frontend"
npm install

ng generate component components/login --skip-tests
ng generate component components/chat --skip-tests
ng generate service services/auth --skip-tests

cp "$PROJECT_DIR/templates/frontend/login.component.ts" src/app/components/login/
cp "$PROJECT_DIR/templates/frontend/login.component.html" src/app/components/login/
cp "$PROJECT_DIR/templates/frontend/login.component.css" src/app/components/login/

cp "$PROJECT_DIR/templates/frontend/chat.component.ts" src/app/components/chat/
cp "$PROJECT_DIR/templates/frontend/chat.component.html" src/app/components/chat/
cp "$PROJECT_DIR/templates/frontend/chat.component.css" src/app/components/chat/

log_success "Frontend ready"

#############################################################################
# PHASE 6: Firewall
#############################################################################

log_info "Configuring Firewall"
ufw --force enable
ufw allow 22/tcp
ufw allow 3000/tcp
ufw allow 4200/tcp
log_success "Firewall configured"

#############################################################################
# PHASE 7: Ready
#############################################################################

cat << 'EOF'

╔════════════════════════════════════════════════════════════════╗
║          Lab 7 - MEAN Stack Setup Complete! 🎉                ║
╚════════════════════════════════════════════════════════════════╝

✓ Node.js & npm installed
✓ MongoDB installed & running
✓ Angular CLI installed
✓ Backend configured
✓ Frontend configured
✓ Firewall configured

🚀 TO START THE APPLICATION:

Terminal 1 - Backend:
  cd ~/Jazz/backend
  npm start

Terminal 2 - Frontend:
  cd ~/Jazz/frontend
  ng serve

Then open: http://localhost:4200

🔧 To update .env:
  nano ~/Jazz/backend/.env

✓ Lab 7 is ready to go!

EOF

log_success "Lab 7 Setup Complete!"
