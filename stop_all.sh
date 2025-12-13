#!/bin/bash

#############################################################################
# Jazz Stop Script
# Stops both backend and frontend services
#############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Stopping Jazz Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Stop backend
if [ -f "$SCRIPT_DIR/backend/backend.pid" ]; then
    BACKEND_PID=$(cat "$SCRIPT_DIR/backend/backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "Stopping Backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        rm "$SCRIPT_DIR/backend/backend.pid"
        echo "✓ Backend stopped"
    else
        echo "⚠ Backend not running"
        rm "$SCRIPT_DIR/backend/backend.pid" 2>/dev/null
    fi
else
    echo "⚠ Backend PID file not found"
fi

# Stop frontend
if [ -f "$SCRIPT_DIR/frontend/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$SCRIPT_DIR/frontend/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "Stopping Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm "$SCRIPT_DIR/frontend/frontend.pid"
        echo "✓ Frontend stopped"
    else
        echo "⚠ Frontend not running"
        rm "$SCRIPT_DIR/frontend/frontend.pid" 2>/dev/null
    fi
else
    echo "⚠ Frontend PID file not found"
fi

# Alternative: kill by port
echo
echo "Checking for processes on ports..."

BACKEND_PORT_PID=$(lsof -ti:3000 2>/dev/null)
if [ ! -z "$BACKEND_PORT_PID" ]; then
    echo "Found process on port 3000 (PID: $BACKEND_PORT_PID)"
    read -p "Kill it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill $BACKEND_PORT_PID
        echo "✓ Killed process on port 3000"
    fi
fi

FRONTEND_PORT_PID=$(lsof -ti:4200 2>/dev/null)
if [ ! -z "$FRONTEND_PORT_PID" ]; then
    echo "Found process on port 4200 (PID: $FRONTEND_PORT_PID)"
    read -p "Kill it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill $FRONTEND_PORT_PID
        echo "✓ Killed process on port 4200"
    fi
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Stop complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
