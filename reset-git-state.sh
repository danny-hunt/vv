#!/bin/bash

# Script to reset git state of folders 1-6 to the latest main branch from remote
# This will discard any uncommitted local changes

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Resetting git state for folders 1-6 ==="
echo ""

for folder in 1 2 3 4 5 6; do
    echo "Processing folder: $folder"
    
    cd "$SCRIPT_DIR/$folder"
    
    # Check if it's a git repository
    if [ ! -d ".git" ]; then
        echo "  ⚠️  Warning: $folder is not a git repository, skipping..."
        echo ""
        continue
    fi
    
    # Fetch latest changes from remote
    echo "  📥 Fetching latest changes from remote..."
    git fetch origin
    
    # Discard local changes and reset to origin/main
    echo "  🔄 Resetting to origin/main..."
    git checkout main --force
    
    # Clean untracked files and directories
    echo "  🧹 Cleaning untracked files..."
    git clean -fd

    git pull
    
    echo "  ✅ Done!"
    echo ""
done

echo "=== All folders reset successfully ==="

