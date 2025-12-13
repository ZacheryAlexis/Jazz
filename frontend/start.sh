#!/bin/bash
# Jazz Frontend Startup Script

cd "$(dirname "$0")"
echo "Starting Jazz Frontend..."
echo "URL: http://localhost:4200"
echo "Press Ctrl+C to stop"
echo
ng serve --host 0.0.0.0
