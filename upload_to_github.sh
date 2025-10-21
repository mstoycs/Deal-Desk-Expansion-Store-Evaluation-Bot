#!/bin/bash

# Script to help upload Eddie to GitHub repository

echo "📦 Preparing to upload Eddie to GitHub..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# GitHub repository URL
REPO_URL="https://github.com/mstoycs/Deal-Desk-Expansion-Store-Evaluation-Bot.git"

echo "This script will help you upload Eddie to your GitHub repository."
echo "Repository: $REPO_URL"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Git is not installed. Please install git first.${NC}"
    exit 1
fi

# Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    echo -e "${GREEN}✓ Git repository initialized${NC}"
else
    echo -e "${YELLOW}Git repository already initialized${NC}"
fi

# Add remote if not already added
if ! git remote | grep -q "origin"; then
    echo "Adding remote origin..."
    git remote add origin $REPO_URL
    echo -e "${GREEN}✓ Remote origin added${NC}"
else
    echo -e "${YELLOW}Remote origin already exists${NC}"
fi

# Create initial commit
echo ""
echo "Preparing files for commit..."

# Add all files
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo -e "${YELLOW}No changes to commit${NC}"
else
    echo "Creating commit..."
    git commit -m "Initial commit: Eddie - Expansion Store Evaluation Bot

    - Core evaluation engine with sophisticated product matching
    - Flask API server with CORS support
    - Web interface for easy interaction
    - Docker support for containerized deployment
    - CI/CD pipelines with GitHub Actions
    - Comprehensive documentation and setup scripts"

    echo -e "${GREEN}✓ Commit created${NC}"
fi

echo ""
echo "========================================="
echo "Ready to push to GitHub!"
echo "========================================="
echo ""
echo "To push to GitHub, run:"
echo -e "${GREEN}git push -u origin main${NC}"
echo ""
echo "If the main branch doesn't exist on GitHub yet, you may need to:"
echo "1. Create it on GitHub first, or"
echo "2. Push to master and then rename: git push -u origin master"
echo ""
echo "After pushing, you can:"
echo "1. Set up GitHub Actions secrets for deployment"
echo "2. Configure branch protection rules"
echo "3. Add collaborators to the repository"
echo "4. Set up webhooks for CI/CD"
echo ""
echo "For repository access, make sure you have:"
echo "- GitHub personal access token configured"
echo "- SSH keys set up for GitHub"
echo "- Proper permissions on the repository"
