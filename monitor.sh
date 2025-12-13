#!/bin/bash

# monitor.sh - Request/Response Logger with PII Censoring
# Logs all HTTP requests and responses with timestamps
# Automatically censors Personally Identifiable Information (PII)

LOG_DIR="/home/zach/Jazz/logs"
REQUEST_LOG="${LOG_DIR}/requests.log"
RESPONSE_LOG="${LOG_DIR}/responses.log"
BACKEND_PORT=3000

# Create logs directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# PII patterns to censor (regex)
declare -A PII_PATTERNS=(
    ["EMAIL"]='[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    ["PHONE"]='(\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}'
    ["SSN"]='\d{3}-\d{2}-\d{4}'
    ["CREDIT_CARD"]='\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
    ["PASSWORD"]='"password"\s*:\s*"[^"]*"'
    ["TOKEN"]='"token"\s*:\s*"[^"]*"'
)

# Function to censor PII in a string
censor_pii() {
    local text="$1"
    
    # Censor emails
    text=$(echo "$text" | sed -E 's/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/***EMAIL_REDACTED***/g')
    
    # Censor phone numbers
    text=$(echo "$text" | sed -E 's/(\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}/***PHONE_REDACTED***/g')
    
    # Censor SSN
    text=$(echo "$text" | sed -E 's/\d{3}-\d{2}-\d{4}/***SSN_REDACTED***/g')
    
    # Censor credit cards
    text=$(echo "$text" | sed -E 's/\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/***CARD_REDACTED***/g')
    
    # Censor passwords (JSON format)
    text=$(echo "$text" | sed -E 's/"password"\s*:\s*"[^"]*"/"password":"***REDACTED***"/g')
    
    # Censor tokens (JSON format)
    text=$(echo "$text" | sed -E 's/"token"\s*:\s*"[^"]{20,}"/"token":"***REDACTED***"/g')
    
    echo "$text"
}

# Function to log request
log_request() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local method="$1"
    local path="$2"
    local headers="$3"
    local body="$4"
    
    # Censor PII in body
    local censored_body=$(censor_pii "$body")
    
    echo "========================================" >> "$REQUEST_LOG"
    echo "TIMESTAMP: $timestamp" >> "$REQUEST_LOG"
    echo "METHOD: $method" >> "$REQUEST_LOG"
    echo "PATH: $path" >> "$REQUEST_LOG"
    echo "HEADERS: $headers" >> "$REQUEST_LOG"
    echo "BODY: $censored_body" >> "$REQUEST_LOG"
    echo "" >> "$REQUEST_LOG"
}

# Function to log response
log_response() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local status="$1"
    local body="$2"
    
    # Censor PII in response body
    local censored_body=$(censor_pii "$body")
    
    echo "========================================" >> "$RESPONSE_LOG"
    echo "TIMESTAMP: $timestamp" >> "$RESPONSE_LOG"
    echo "STATUS: $status" >> "$RESPONSE_LOG"
    echo "BODY: $censored_body" >> "$RESPONSE_LOG"
    echo "" >> "$RESPONSE_LOG"
}

# Function to monitor backend logs
monitor_backend_logs() {
    echo "Starting monitor.sh - Logging requests and censoring PII"
    echo "Request log: $REQUEST_LOG"
    echo "Response log: $RESPONSE_LOG"
    echo "Monitoring backend on port $BACKEND_PORT..."
    echo ""
    
    # Monitor backend access logs (if using morgan or similar)
    if [ -f "/home/zach/Jazz/backend/backend.log" ]; then
        tail -f /home/zach/Jazz/backend/backend.log | while read -r line; do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            censored_line=$(censor_pii "$line")
            echo "[$timestamp] $censored_line" | tee -a "$REQUEST_LOG"
        done
    else
        echo "Backend log file not found. Monitoring network traffic instead..."
        
        # Alternative: Monitor network traffic (requires tcpdump)
        if command -v tcpdump &> /dev/null; then
            sudo tcpdump -i lo -A -s 0 "tcp port $BACKEND_PORT" 2>/dev/null | \
            while read -r line; do
                censored_line=$(censor_pii "$line")
                echo "$censored_line" >> "$REQUEST_LOG"
            done
        else
            echo "ERROR: Cannot monitor traffic. Install tcpdump or configure backend logging."
            echo "To enable backend logging, add morgan middleware to server.js"
        fi
    fi
}

# Function to display recent logs
show_recent_logs() {
    echo "Recent Requests (last 20 lines):"
    echo "================================"
    tail -20 "$REQUEST_LOG" 2>/dev/null || echo "No requests logged yet"
    echo ""
    echo "Recent Responses (last 20 lines):"
    echo "================================="
    tail -20 "$RESPONSE_LOG" 2>/dev/null || echo "No responses logged yet"
}

# Main execution
case "${1:-monitor}" in
    monitor)
        monitor_backend_logs
        ;;
    show)
        show_recent_logs
        ;;
    test)
        # Test PII censoring
        echo "Testing PII censoring..."
        test_data='{"email":"user@example.com","password":"secret123","phone":"555-123-4567"}'
        echo "Original: $test_data"
        echo "Censored: $(censor_pii "$test_data")"
        ;;
    *)
        echo "Usage: $0 {monitor|show|test}"
        echo "  monitor - Start monitoring and logging (default)"
        echo "  show    - Display recent logs"
        echo "  test    - Test PII censoring"
        exit 1
        ;;
esac
