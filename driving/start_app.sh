#!/bin/bash

# Interactive Driving Study Hub Startup Script
echo "🚗 Starting Interactive Driving Study Hub..."
echo "==============================================="

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed. Please install Python3 first."
    exit 1
fi

# Check if required Python packages are installed
echo "📦 Checking Python dependencies..."
python3 -c "import flask, flask_cors, sqlite3" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required Python packages..."
    pip3 install flask flask-cors
fi

# Change to the app directory
cd "$(dirname "$0")"

# Check if database exists
if [ ! -f "driving_study_material.db" ]; then
    echo "❌ Database not found. Please ensure the database is set up properly."
    exit 1
fi

echo "🚀 Starting Flask backend server..."
# Start the backend server in the background
python3 backend.py &
BACKEND_PID=$!

# Wait a moment for the server to start
sleep 3

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend server started successfully (PID: $BACKEND_PID)"
else
    echo "❌ Failed to start backend server"
    exit 1
fi

echo "🌐 Opening the application in your default browser..."
echo ""
echo "📚 Application Features:"
echo "   • Study sections with interactive content"
echo "   • Flashcards for quick review"
echo "   • Comprehensive quiz system"
echo "   • Progress tracking"
echo "   • Search functionality"
echo ""
echo "🔗 Access URLs:"
echo "   • Main App: file://$(pwd)/enhanced_driving.html"
echo "   • API Base: http://localhost:5001/api"
echo ""

# Open the HTML file in default browser
if command -v open &> /dev/null; then
    # macOS
    open "enhanced_driving.html"
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "enhanced_driving.html"
elif command -v start &> /dev/null; then
    # Windows
    start "enhanced_driving.html"
else
    echo "Please manually open: $(pwd)/enhanced_driving.html"
fi

echo ""
echo "⚠️  Important: Keep this terminal window open to keep the backend running."
echo "   Press Ctrl+C to stop the application."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down the application..."
    kill $BACKEND_PID 2>/dev/null
    echo "✅ Backend server stopped."
    echo "👋 Thank you for using Interactive Driving Study Hub!"
    exit 0
}

# Set up signal handling
trap cleanup INT TERM

# Keep the script running
echo "✅ Application is now running. Waiting for shutdown signal..."
wait $BACKEND_PID
