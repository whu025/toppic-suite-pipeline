#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

echo "=== Starting TopPIC Suite Web Console ==="

# Free port 8000 if currently occupied by a previous process
fuser -k 8000/tcp 2>/dev/null || true

# Activate virtual environment if present
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the FastAPI application using Uvicorn
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload