#!/bin/bash

# Start Eddie in local development mode

set -e

echo "🚀 Starting Eddie in local mode..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found. Please run ./scripts/setup.sh first${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default port if not specified
FLASK_PORT=${FLASK_PORT:-5001}

# Check if port is already in use
if lsof -Pi :$FLASK_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Port $FLASK_PORT is already in use${NC}"
    echo "Would you like to:"
    echo "1) Kill the existing process and start Eddie"
    echo "2) Use a different port"
    echo "3) Cancel"
    read -p "Enter choice (1-3): " choice
    
    case $choice in
        1)
            echo "Killing existing process on port $FLASK_PORT..."
            lsof -ti:$FLASK_PORT | xargs kill -9 2>/dev/null || true
            sleep 2
            ;;
        2)
            read -p "Enter new port number: " FLASK_PORT
            export FLASK_PORT
            ;;
        3)
            echo "Cancelled"
            exit 0
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
fi

# Start Flask app
echo -e "${GREEN}Starting Flask app on port $FLASK_PORT...${NC}"
echo "Log file: flask_startup.log"
echo ""

# Run Flask with proper output
python app.py 2>&1 | tee flask_startup.log &
FLASK_PID=$!

# Wait for Flask to start
echo "Waiting for Flask to start..."
for i in {1..10}; do
    if curl -s http://localhost:$FLASK_PORT/health > /dev/null; then
        echo -e "${GREEN}✓ Flask is running!${NC}"
        break
    fi
    sleep 1
done

echo ""
echo "========================================="
echo -e "${GREEN}Eddie is running!${NC}"
echo "========================================="
echo ""
echo "Access Eddie at:"
echo "  - API: http://localhost:$FLASK_PORT"
echo "  - Web UI: Open eddie_localhost.html in your browser"
echo ""
echo "To stop Eddie, press Ctrl+C or run ./scripts/stop_local.sh"
echo ""
echo "Monitoring logs (Ctrl+C to exit)..."
echo ""

# Keep the script running and show logs
tail -f flask_startup.log

# Cleanup on exit
trap "kill $FLASK_PID 2>/dev/null; echo 'Eddie stopped'" EXIT
