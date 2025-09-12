#!/bin/bash

# Eddie Platform Setup Script
# This script sets up the Eddie platform for local development

set -e  # Exit on error

echo "🚀 Setting up Eddie Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    REQUIRED_VERSION="3.9"
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        print_status "Python $PYTHON_VERSION found"
    else
        print_error "Python $REQUIRED_VERSION or higher required. Found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.9 or higher"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
print_status "Virtual environment activated"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_status "pip upgraded"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
print_status "Dependencies installed"

# Create .env file from template
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp env.template .env
    print_status ".env file created"
    print_warning "Please update .env with your configuration"
else
    print_warning ".env file already exists. Skipping..."
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs data static templates tests deployment/scripts
print_status "Directories created"

# Check if dynamic_knowledge_base.json exists
if [ ! -f dynamic_knowledge_base.json ]; then
    echo "Creating empty dynamic_knowledge_base.json..."
    echo '{"stores": {}, "products": {}, "collections": {}}' > dynamic_knowledge_base.json
    print_status "dynamic_knowledge_base.json created"
fi

# Run basic health check
echo "Running health check..."
python3 -c "import flask; import requests; import cv2; print('All core modules imported successfully')" 2>/dev/null
if [ $? -eq 0 ]; then
    print_status "Health check passed"
else
    print_error "Health check failed. Some modules may not be installed correctly"
fi

echo ""
echo "========================================="
echo "✅ Eddie Platform setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Update .env with your configuration"
echo "2. Run './scripts/start_local.sh' to start Eddie locally"
echo "3. Or run 'docker-compose up' to start with Docker"
echo ""
echo "For more information, see README.md"

