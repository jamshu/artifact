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
