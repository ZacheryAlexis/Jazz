#!/bin/bash
# Jazz Backend Startup Script

cd "$(dirname "$0")"
echo "Starting Jazz Backend..."
echo "MongoDB: mongodb://localhost:27017/jazz"
echo "Port: 3000"
echo "Press Ctrl+C to stop"
echo
npm start
