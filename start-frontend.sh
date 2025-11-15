#!/bin/bash

# Start the VV frontend

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the dev server
echo "Starting VV frontend on http://localhost:5173"
npm run dev

