#!/bin/bash
# POS Geidea Logging Server - Unix Installation Script
# Works on Linux, macOS, and other Unix-like systems

set -e  # Exit on any error

echo "========================================"
echo "POS Geidea Logging Server Installation"
echo "========================================"
echo

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    echo "Please install Python 3.8+ using your system package manager:"
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip python3-venv"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "  macOS: brew install python3"
    exit 1
fi

echo -e "${GREEN}✅ Python found:${NC}"
python3 --version

# Check if pip is available
if ! python3 -m pip --version &> /dev/null; then
    echo -e "${RED}ERROR: pip is not available${NC}"
    echo "Please install pip:"
    echo "  Ubuntu/Debian: sudo apt install python3-pip"
    echo "  CentOS/RHEL: sudo yum install python3-pip"
    echo "  macOS: python3 -m ensurepip --upgrade"
    exit 1
fi

echo -e "${GREEN}✅ pip found:${NC}"
python3 -m pip --version

# Create virtual environment
echo
echo -e "${BLUE}📦 Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo "Virtual environment already exists, removing old one..."
    rm -rf venv
fi

python3 -m venv venv
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to create virtual environment${NC}"
    exit 1
fi

# Activate virtual environment
echo
echo -e "${BLUE}⚡ Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo
echo -e "${BLUE}📥 Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to install dependencies${NC}"
    exit 1
fi

echo
echo -e "${GREEN}✅ Installation completed successfully!${NC}"
echo

# Create startup script
echo -e "${BLUE}🚀 Creating startup scripts...${NC}"

# Create start_server.sh
cat > start_server.sh << 'EOF'
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
EOF

chmod +x start_server.sh

# Create systemd service file for Linux
if command -v systemctl &> /dev/null; then
    CURRENT_DIR=$(pwd)
    USER=$(whoami)
    
    cat > pos-geidea-logging.service << EOF
[Unit]
Description=POS Geidea Logging Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Create service installation script
    cat > install_service.sh << 'EOF'
#!/bin/bash
# Install POS Geidea Logging Server as systemd service
# Run with sudo

if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "Installing POS Geidea Logging Server as systemd service..."

# Copy service file
cp pos-geidea-logging.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable and start service
systemctl enable pos-geidea-logging.service
systemctl start pos-geidea-logging.service

echo
echo "✅ Service installed and started!"
echo "The logging server will now start automatically on boot."
echo
echo "Service commands:"
echo "  sudo systemctl status pos-geidea-logging    # Check status"
echo "  sudo systemctl stop pos-geidea-logging      # Stop service"
echo "  sudo systemctl start pos-geidea-logging     # Start service"
echo "  sudo systemctl restart pos-geidea-logging   # Restart service"
echo "  sudo systemctl disable pos-geidea-logging   # Disable auto-start"
EOF

    chmod +x install_service.sh
    echo -e "${GREEN}✅ Created install_service.sh - Run with sudo to install as systemd service${NC}"
fi

# Create macOS LaunchAgent for auto-start
if [[ "$OSTYPE" == "darwin"* ]]; then
    CURRENT_DIR=$(pwd)
    USER=$(whoami)
    
    mkdir -p ~/Library/LaunchAgents
    
    cat > ~/Library/LaunchAgents/com.pos.geidea.logging.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pos.geidea.logging</string>
    <key>ProgramArguments</key>
    <array>
        <string>$CURRENT_DIR/venv/bin/python</string>
        <string>$CURRENT_DIR/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$CURRENT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>$CURRENT_DIR/logs/error.log</string>
    <key>StandardOutPath</key>
    <string>$CURRENT_DIR/logs/output.log</string>
</dict>
</plist>
EOF

    # Create macOS service management script
    cat > install_macos_service.sh << 'EOF'
#!/bin/bash
# Install POS Geidea Logging Server as macOS LaunchAgent

echo "Installing POS Geidea Logging Server as macOS LaunchAgent..."

# Load the service
launchctl load ~/Library/LaunchAgents/com.pos.geidea.logging.plist

echo
echo "✅ Service installed and started!"
echo "The logging server will now start automatically when you log in."
echo
echo "Service commands:"
echo "  launchctl list | grep pos.geidea        # Check if running"
echo "  launchctl stop com.pos.geidea.logging   # Stop service"
echo "  launchctl start com.pos.geidea.logging  # Start service"
echo "  launchctl unload ~/Library/LaunchAgents/com.pos.geidea.logging.plist  # Remove service"
EOF

    chmod +x install_macos_service.sh
    echo -e "${GREEN}✅ Created install_macos_service.sh - Run to install as macOS LaunchAgent${NC}"
fi

echo -e "${GREEN}✅ Created start_server.sh - Run to start the server manually${NC}"
echo

# Ask user if they want to start the server now
echo -e "${YELLOW}Do you want to start the logging server now? (y/N):${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo
    echo -e "${BLUE}🚀 Starting POS Geidea Logging Server...${NC}"
    echo "Dashboard: http://localhost:8000/"
    echo "API Docs: http://localhost:8000/docs"
    echo "Press Ctrl+C to stop the server"
    echo
    python main.py
else
    echo
    echo -e "${BLUE}📋 To start the server later, run: ./start_server.sh${NC}"
    if command -v systemctl &> /dev/null; then
        echo -e "${BLUE}📋 To install as systemd service, run: sudo ./install_service.sh${NC}"
    fi
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${BLUE}📋 To install as macOS service, run: ./install_macos_service.sh${NC}"
    fi
fi

echo
echo -e "${GREEN}Installation completed!${NC}"