#!/bin/bash

# Quick script to push Eddie to the correct GitHub repository
# Repository: https://github.com/mstoycs/Deal-Desk-Expansion-Store-Evaluation-Bot.git

echo "🚀 Quick Push to GitHub - Eddie Platform"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Correct repository URL
REPO_URL="https://github.com/mstoycs/Deal-Desk-Expansion-Store-Evaluation-Bot.git"

echo "Target repository: $REPO_URL"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}Error: app.py not found. Are you in the Eddie-GitHub-Package directory?${NC}"
    echo "Please run: cd /Users/mattstoycos/Eddie-GitHub-Package"
    exit 1
fi

# Initialize git if needed
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    echo -e "${GREEN}✓ Git initialized${NC}"
fi

# Remove any existing remote and add the correct one
echo "Setting up correct remote..."
git remote remove origin 2>/dev/null
git remote add origin $REPO_URL
echo -e "${GREEN}✓ Remote configured to: mstoycs/Deal-Desk-Expansion-Store-Evaluation-Bot${NC}"

# Add all files
echo ""
echo "Adding all files..."
git add .
echo -e "${GREEN}✓ Files staged${NC}"

# Create commit if there are changes
if ! git diff --staged --quiet; then
    echo ""
    echo "Creating commit..."
    git commit -m "Add Eddie - Expansion Store Evaluation Bot

Complete platform with:
- Core evaluation engine
- Flask API server
- Web interface
- Docker support
- CI/CD pipelines
- Comprehensive documentation"
    echo -e "${GREEN}✓ Commit created${NC}"
else
    echo -e "${YELLOW}No changes to commit${NC}"
fi

# Push to GitHub
echo ""
echo "========================================="
echo -e "${GREEN}Ready to push!${NC}"
echo "========================================="
echo ""
echo "To push to your GitHub repository, run:"
echo ""
echo -e "${GREEN}git push -u origin main${NC}"
echo ""
echo "If that fails (no main branch), try:"
echo -e "${GREEN}git push -u origin master${NC}"
echo ""
echo "Or to create main branch:"
echo -e "${GREEN}git branch -M main${NC}"
echo -e "${GREEN}git push -u origin main${NC}"
echo ""
echo "If you need to force push (overwrite remote):"
echo -e "${YELLOW}git push -u origin main --force${NC}"
echo ""
echo -e "${GREEN}Repository URL: https://github.com/mstoycs/Deal-Desk-Expansion-Store-Evaluation-Bot${NC}"

