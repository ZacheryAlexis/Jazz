#!/bin/bash

#############################################################################
# Jazz Status Check
# Shows status of all Jazz services
#############################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Jazz Services Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# MongoDB
echo "MongoDB:"
if systemctl is-active --quiet mongod; then
    echo "  ✓ Running"
    echo "  Port: 27017"
else
    echo "  ✗ Not running"
fi
echo

# Backend
echo "Backend:"
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    BACKEND_PID=$(lsof -ti:3000)
    echo "  ✓ Running"
    echo "  Port: 3000"
    echo "  PID: $BACKEND_PID"
    echo "  URL: http://localhost:3000"
else
    echo "  ✗ Not running"
fi
echo

# Frontend
echo "Frontend:"
if lsof -Pi :4200 -sTCP:LISTEN -t >/dev/null 2>&1; then
    FRONTEND_PID=$(lsof -ti:4200)
    echo "  ✓ Running"
    echo "  Port: 4200"
    echo "  PID: $FRONTEND_PID"
    echo "  URL: http://localhost:4200"
else
    echo "  ✗ Not running"
fi
echo

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Commands:"
echo "  Start: ./start_all.sh"
echo "  Stop:  ./stop_all.sh"
echo "  Logs:  tail -f backend/backend.log"
echo "         tail -f frontend/frontend.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
