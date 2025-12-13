#!/bin/bash

#############################################################################
# Jazz Complete Startup Script
# Starts both backend and frontend in background
#############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Starting Jazz MEAN Stack"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Check if MongoDB is running
if ! systemctl is-active --quiet mongod; then
    echo "Starting MongoDB..."
    sudo systemctl start mongod
fi

echo "✓ MongoDB is running"

# Check if services are already running
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠ Backend already running on port 3000"
else
    echo "Starting Backend (port 3000)..."
    cd "$SCRIPT_DIR/backend"
    nohup npm start > backend.log 2>&1 &
    echo $! > backend.pid
    echo "  Backend PID: $(cat backend.pid)"
    sleep 2
fi

if lsof -Pi :4200 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠ Frontend already running on port 4200"
else
    echo "Starting Frontend (port 4200)..."
    cd "$SCRIPT_DIR/frontend"
    nohup ng serve --host 0.0.0.0 > frontend.log 2>&1 &
    echo $! > frontend.pid
    echo "  Frontend PID: $(cat frontend.pid)"
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Jazz services started!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "Services:"
echo "  • Backend API: http://localhost:3000"
echo "  • Frontend UI: http://localhost:4200"
echo "  • MongoDB: mongodb://localhost:27017/jazz"
echo
echo "Logs:"
echo "  • Backend:  tail -f $SCRIPT_DIR/backend/backend.log"
echo "  • Frontend: tail -f $SCRIPT_DIR/frontend/frontend.log"
echo
echo "To stop services:"
echo "  cd $SCRIPT_DIR && ./stop_all.sh"
echo
