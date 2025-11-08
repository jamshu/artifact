#!/bin/bash
# Start POS Geidea Logging Server

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting POS Geidea Logging Server..."
echo "Dashboard: http://localhost:8000/"
echo "API Docs: http://localhost:8000/docs"
echo "Press Ctrl+C to stop the server"
echo

python main.py
