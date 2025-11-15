#!/bin/bash

# Test script for merge conflict resolution
# This script sets up a simple conflict scenario for testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Merge Conflict Resolution Test Setup ==="
echo ""

# Check if panes 1 and 2 exist
if [ ! -d "$SCRIPT_DIR/1" ] || [ ! -d "$SCRIPT_DIR/2" ]; then
    echo "❌ Error: Panes 1 and 2 must exist"
    echo "   Please create them using the UI first"
    exit 1
fi

# Check if both are on main branch
cd "$SCRIPT_DIR/1"
if [ "$(git branch --show-current)" != "main" ]; then
    echo "❌ Error: Pane 1 must be on main branch"
    echo "   Current branch: $(git branch --show-current)"
    echo "   Please close the pane in the UI to reset to main"
    exit 1
fi

cd "$SCRIPT_DIR/2"
if [ "$(git branch --show-current)" != "main" ]; then
    echo "❌ Error: Pane 2 must be on main branch"
    echo "   Current branch: $(git branch --show-current)"
    echo "   Please close the pane in the UI to reset to main"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Step 1: Create and merge change in pane 1
echo "Step 1: Creating change in pane 1..."
cd "$SCRIPT_DIR/1"

# Create a temporary branch
git checkout -b tmp-test-1

# Make a change to App.css
if [ -f "src/App.css" ]; then
    echo "/* Test change from pane 1 */" >> src/App.css
    echo ".test-class-1 { color: red; }" >> src/App.css
else
    echo "⚠️  Warning: src/App.css not found in pane 1"
    echo "   Creating it..."
    mkdir -p src
    echo ".test-class-1 { color: red; }" > src/App.css
fi

git add -A
git commit -m "Test change 1"

# Merge to main
git checkout main
git merge tmp-test-1 --no-ff -m "Merge test change 1"
git push origin main
git branch -D tmp-test-1

echo "✅ Change in pane 1 merged to main"
echo ""

# Step 2: Create conflicting change in pane 2
echo "Step 2: Creating conflicting change in pane 2..."
cd "$SCRIPT_DIR/2"

# Pull latest from main first
git pull origin main

# Create a temporary branch
git checkout -b tmp-test-2

# Make a CONFLICTING change to the same file
if [ -f "src/App.css" ]; then
    echo "/* Test change from pane 2 - CONFLICTS with pane 1 */" >> src/App.css
    echo ".test-class-1 { color: blue; }" >> src/App.css
else
    echo "⚠️  Warning: src/App.css not found in pane 2"
    mkdir -p src
    echo ".test-class-1 { color: blue; }" > src/App.css
fi

git add -A
git commit -m "Test change 2 (will conflict)"

echo "✅ Conflicting change created in pane 2"
echo ""

echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. In the UI, create pane 2 (if not already active)"
echo "2. The pane should show 'Ahead' badge"
echo "3. Click the 'Merge' button on pane 2"
echo "4. Watch the backend logs for conflict resolution:"
echo "   tail -f <backend-log-file> | grep -i conflict"
echo ""
echo "Expected outcome:"
echo "- Backend detects merge conflict"
echo "- cursor-agent is invoked automatically"
echo "- Agent resolves the conflict"
echo "- Merge completes successfully"
echo "- Pane 2 returns to main branch"
echo ""
echo "To verify after merge:"
echo "  cd 2"
echo "  git status    # Should be clean on main"
echo "  git log -1    # Should show merge commit"
echo ""
echo "To clean up:"
echo "  ./reset-git-state.sh"

