#!/bin/bash

# PDF/PNG Web Compression Interface Startup Script
# This script starts the Flask web server for easy PDF/PNG compression

echo "🚀 Starting PDF/PNG Web Compression Interface..."
echo "=============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3."
    exit 1
fi

# Check if pip3 is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not found. Please install pip3."
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found in current directory."
    exit 1
fi

# Install/update dependencies
echo "📦 Installing/updating Python dependencies..."
pip3 install -r requirements.txt

# Check if poppler is installed (needed for PDF processing)
if ! command -v pdftoppm &> /dev/null; then
    echo "⚠️  Warning: poppler not found. PDF conversion may not work."
    echo "   On macOS, install with: brew install poppler"
    echo "   On Linux, install with: sudo apt-get install poppler-utils"
fi

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found in current directory."
    exit 1
fi

# Create necessary directories
mkdir -p uploads outputs

echo ""
echo "✅ All checks passed! Starting the web server..."
echo ""
echo "📱 Web Interface Access:"
echo "   Local:    http://localhost:5000"
echo "   Network:  http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo 'your-ip'):5000"
echo ""
echo "🎯 Features:"
echo "   • Upload PDF or PNG files"
echo "   • Automatic compression to under 3.6 KB"
echo "   • Drag & drop support"
echo "   • Mobile-friendly interface"
echo ""
echo "🛑 To stop the server: Press Ctrl+C"
echo "=============================================="
echo ""

# Start the Flask application
python3 app.py