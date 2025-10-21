#!/bin/bash

# Force push Eddie to GitHub (replaces all remote content)

echo "⚠️  FORCE PUSH TO GITHUB - EDDIE PLATFORM"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}WARNING: This will replace ALL content on the remote repository!${NC}"
echo "Remote: https://github.com/mstoycs/Deal-Desk-Expansion-Store-Evaluation-Bot.git"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Force pushing to GitHub..."
git push -u origin main --force

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ SUCCESS! Eddie platform has been pushed to GitHub!${NC}"
    echo ""
    echo "Your repository is now live at:"
    echo -e "${GREEN}https://github.com/mstoycs/Deal-Desk-Expansion-Store-Evaluation-Bot${NC}"
    echo ""
    echo "All previous content has been replaced with the Eddie platform."
else
    echo -e "${RED}❌ Push failed. Please check your credentials and try again.${NC}"
fi
