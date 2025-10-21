#!/bin/bash

# Stop Eddie and clean up processes

echo "🛑 Stopping Eddie..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to kill processes
kill_process() {
    local process_name=$1
    local port=$2

    if [ -n "$port" ]; then
        # Kill by port
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
            echo -e "${GREEN}✓${NC} Stopped process on port $port"
        fi
    else
        # Kill by name
        pkill -f "$process_name" 2>/dev/null || true
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} Stopped $process_name"
        fi
    fi
}

# Stop Flask app
echo "Stopping Flask app..."
kill_process "app.py" 5001
kill_process "app.py" 5000
kill_process "flask" ""
kill_process "gunicorn" ""

# Stop any Docker containers
if command -v docker &> /dev/null; then
    if docker ps | grep -q eddie; then
        echo "Stopping Docker containers..."
        docker-compose down 2>/dev/null || docker stop eddie-bot 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Docker containers stopped"
    fi
fi

# Clean up any orphaned Python processes
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*expansion_store_evaluator" 2>/dev/null || true

# Check if any Eddie processes are still running
if pgrep -f "app.py|flask|eddie" > /dev/null; then
    echo -e "${YELLOW}⚠${NC} Some Eddie processes may still be running:"
    ps aux | grep -E "app.py|flask|eddie" | grep -v grep
    echo ""
    read -p "Force kill all remaining processes? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -9 -f "app.py|flask|eddie" 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Force killed remaining processes"
    fi
else
    echo -e "${GREEN}✓${NC} All Eddie processes stopped"
fi

echo ""
echo "========================================="
echo -e "${GREEN}Eddie has been stopped${NC}"
echo "========================================="
