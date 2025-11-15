#!/bin/bash

# Start the VV backend server

cd backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies if needed
pip install -r requirements.txt > /dev/null 2>&1

# Start the server
echo "Starting VV backend on http://localhost:8000"
python main.py

