# POS Geidea Logging Server

A comprehensive logging solution for debugging POS Geidea payment terminal issues. This system captures all console logs, payment events, terminal interactions, and JavaScript errors, storing them in a local SQLite database for future analysis.

## 🚀 Quick Start

### Windows
1. Download/copy the `logging_server` folder
2. Double-click `install_windows.bat`
3. Follow the prompts (installs Python dependencies and starts server)
4. Access dashboard at http://localhost:8000/

### Linux/macOS/Unix
1. Download/copy the `logging_server` folder  
2. Run: `chmod +x install_unix.sh && ./install_unix.sh`
3. Follow the prompts
4. Access dashboard at http://localhost:8000/

## 📋 Features

### 🔍 **Comprehensive Logging**
- **Console Logs**: All Geidea-related console messages
- **Payment Events**: Status changes, terminal interactions
- **Navigation Restrictions**: When and why navigation is blocked
- **JavaScript Errors**: Unhandled errors and promise rejections
- **Session Tracking**: User sessions with context data

### 📊 **Real-time Dashboard**
- Live log viewing with filtering
- Statistics and analytics
- Session management
- Error highlighting
- Export functionality

### 💾 **SQLite Database Storage**
- Fast, local storage
- Indexed for performance
- Session tracking
- Data integrity

### 🔄 **Automatic Logging**
- Batch processing for performance
- Offline queuing
- Auto-retry failed requests
- Background processing

## 📁 Architecture

```
logging_server/
├── main.py                 # FastAPI server
├── requirements.txt        # Python dependencies
├── install_windows.bat     # Windows installer
├── install_unix.sh         # Unix/Linux/macOS installer
├── README.md              # This documentation
└── logs/                  # Exported logs directory
```

## 🔧 Installation

### Requirements
- **Python 3.8+** 
- **pip** (Python package manager)
- **Internet connection** (for initial setup)

### Automatic Installation

#### Windows 10/11
```batch
# Download logging_server folder
# Right-click install_windows.bat -> "Run as administrator"
# OR double-click install_windows.bat
```

#### Linux (Ubuntu/Debian/CentOS)
```bash
# Make executable and run
chmod +x install_unix.sh
./install_unix.sh
```

#### macOS
```bash
# Make executable and run
chmod +x install_unix.sh
./install_unix.sh
```

### Manual Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install -r requirements.txt

# Start server
python main.py
```

## 🖥️ Usage

### Starting the Server

#### Quick Start
- **Windows**: Double-click `start_server.bat`
- **Unix**: Run `./start_server.sh`

#### Manual Start
```bash
python main.py
```

### Accessing the Dashboard
Open your browser to: **http://localhost:8000/**

### API Documentation
Interactive API docs: **http://localhost:8000/docs**

## 🌐 API Endpoints

### Logging Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/logs` | Send single log entry |
| POST | `/api/logs/batch` | Send multiple log entries |
| GET | `/api/logs` | Retrieve logs with filters |
| DELETE | `/api/logs` | Clear logs |

### Management Endpoints  
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions` | Get active sessions |
| GET | `/api/stats` | Get logging statistics |
| GET | `/api/export/{session_id}` | Export session logs |
| GET | `/health` | Health check |

### Example API Usage

#### Send Log Entry
```javascript
fetch('http://localhost:8000/api/logs', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        session_id: 'pos_123456_abc',
        component: 'payment',
        level: 'INFO',
        message: 'Payment processed successfully',
        data: {
            amount: 150.00,
            card_type: 'VISA',
            status: 'approved'
        }
    })
});
```

#### Retrieve Logs
```javascript
// Get recent error logs
fetch('http://localhost:8000/api/logs?level=ERROR&limit=50')
    .then(response => response.json())
    .then(data => console.log(data.logs));

// Get logs for specific session
fetch('http://localhost:8000/api/logs?session_id=pos_123456_abc')
    .then(response => response.json())
    .then(data => console.log(data.logs));
```

## 📈 Dashboard Features

### Real-time Monitoring
- **Live Updates**: Auto-refresh every 10 seconds
- **Filtering**: By session, component, level, date range
- **Search**: Full-text search in log messages
- **Export**: Download session logs as JSON

### Statistics Panel
- Total log count
- Active sessions
- Error counts
- Component breakdown

### Log Viewer
- Color-coded by log level
- Expandable JSON data
- Session tracking
- Timestamp sorting

## 🔄 Integration with POS

### Automatic Integration
The logging client automatically integrates with your POS Geidea module:

1. **Console Monitoring**: Captures all Geidea-related console messages
2. **Payment Events**: Logs payment status changes
3. **Terminal Interactions**: Records terminal communication
4. **Navigation Restrictions**: Tracks when restrictions are applied
5. **Error Handling**: Catches JavaScript errors and exceptions

### Manual Logging
Use the global `geideaLogger` object for custom logging:

```javascript
// Log payment event
window.geideaLogger.logPayment('send_to_terminal', 'waiting', {
    amount: 150.00,
    payment_method: 'Geidea Terminal'
});

// Log terminal interaction
window.geideaLogger.logTerminal('connection', 'Terminal connected', {
    port: 8000,
    connection_mode: 'TCP'
});

// Log navigation restriction
window.geideaLogger.logRestriction('back_button', true, 'Payment in progress');

// Custom component logging
window.geideaLogger.logInfo('custom_component', 'Custom message', {
    custom_data: 'value'
});
```

## 🛠️ Service Installation

### Windows Service
```batch
# Run as Administrator
install_service.bat
```

### Linux systemd Service
```bash
# Run with sudo
sudo ./install_service.sh

# Service management
sudo systemctl status pos-geidea-logging
sudo systemctl start pos-geidea-logging
sudo systemctl stop pos-geidea-logging
```

### macOS LaunchAgent
```bash
./install_macos_service.sh

# Service management
launchctl list | grep pos.geidea
launchctl stop com.pos.geidea.logging
launchctl start com.pos.geidea.logging
```

## 📊 Database Schema

### pos_logs Table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| log_id | TEXT | Unique log identifier |
| session_id | TEXT | POS session ID |
| order_id | TEXT | Current order ID |
| user_id | TEXT | User ID |
| component | TEXT | Component name |
| level | TEXT | Log level (DEBUG/INFO/WARNING/ERROR) |
| message | TEXT | Log message |
| data | TEXT | JSON additional data |
| timestamp | DATETIME | Client timestamp |
| server_timestamp | DATETIME | Server timestamp |
| url | TEXT | Browser URL |
| user_agent | TEXT | Browser user agent |

### pos_sessions Table
| Column | Type | Description |
|--------|------|-------------|
| session_id | TEXT | Primary key |
| user_id | TEXT | User ID |
| start_time | DATETIME | Session start |
| last_activity | DATETIME | Last activity |
| user_agent | TEXT | Browser user agent |
| status | TEXT | Session status |

## 🔍 Troubleshooting

### Server Won't Start
```bash
# Check if port 8000 is in use
netstat -an | grep 8000  # Linux/Mac
netstat -an | findstr 8000  # Windows

# Kill existing process
pkill -f "python main.py"  # Linux/Mac
taskkill /f /im python.exe  # Windows
```

### Database Issues
```bash
# Check database file
ls -la pos_geidea_logs.db  # Linux/Mac
dir pos_geidea_logs.db     # Windows

# Reset database (CAUTION: Deletes all logs)
rm pos_geidea_logs.db      # Linux/Mac
del pos_geidea_logs.db     # Windows
```

### Connection Issues
1. **Check server is running**: Visit http://localhost:8000/health
2. **Check firewall**: Ensure port 8000 is not blocked
3. **Check CORS**: Server allows all origins for local development
4. **Check logs**: Look at server console output for errors

### Log Client Issues
```javascript
// Check client status
console.log(window.geideaLogger.getSessionInfo());

// Force flush logs
window.geideaLogger.flush();

// Test server connection
fetch('http://localhost:8000/health')
    .then(r => r.json())
    .then(data => console.log('Server status:', data));
```

## 🔧 Configuration

### Environment Variables
```bash
export GEIDEA_LOG_SERVER_URL=http://localhost:8000  # Server URL
export GEIDEA_LOG_BATCH_SIZE=10                     # Batch size
export GEIDEA_LOG_FLUSH_INTERVAL=5000               # Flush interval (ms)
```

### Server Configuration
Edit `main.py` to customize:
- **Port**: Change `port=8000` in `uvicorn.run()`
- **Host**: Change `host="0.0.0.0"` for network access
- **Database**: Change `DB_FILE` for custom database location
- **Batch Size**: Adjust logging client batch size

## 📜 Log Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **DEBUG** | Detailed diagnostic info | Development debugging |
| **INFO** | General information | Normal operation events |
| **WARNING** | Something unexpected | Non-critical issues |
| **ERROR** | Error occurred | Critical issues requiring attention |

## 🚀 Performance

### Optimization Tips
- **Batch Size**: Increase for high-volume logging
- **Flush Interval**: Decrease for real-time logging
- **Database**: Use SSD storage for better performance
- **Filtering**: Use specific filters to reduce query load

### Monitoring
- Check `/api/stats` for performance metrics
- Monitor queue length with `geideaLogger.getSessionInfo()`
- Watch database size growth
- Monitor server CPU/memory usage

## 🛡️ Security

### Local Development
- Server binds to all interfaces (`0.0.0.0`)
- CORS allows all origins
- No authentication required
- **Not suitable for production use**

### Production Considerations
- Add authentication/authorization
- Restrict CORS origins
- Use HTTPS
- Implement rate limiting
- Regular log cleanup

## 📝 Maintenance

### Log Cleanup
```bash
# Clear old logs (keep last 30 days)
curl -X DELETE "http://localhost:8000/api/logs?older_than_days=30"

# Clear all logs
curl -X DELETE "http://localhost:8000/api/logs"
```

### Database Maintenance
```sql
-- Manual database queries
sqlite3 pos_geidea_logs.db

-- Get table info
.schema pos_logs

-- Check database size
.databases

-- Vacuum database
VACUUM;
```

### Backup
```bash
# Backup database
cp pos_geidea_logs.db backup_$(date +%Y%m%d).db

# Export logs to JSON
curl "http://localhost:8000/api/logs?limit=10000" > logs_backup.json
```

## 📞 Support

### Log Files
- **Server logs**: Console output
- **Error logs**: `logs/error.log` (if using service)
- **Access logs**: Server console

### Debug Mode
```bash
# Start with debug logging
python main.py --log-level debug
```

### Common Issues
1. **Port in use**: Change port or stop conflicting service
2. **Permission denied**: Run as administrator/sudo for service install
3. **Python not found**: Install Python 3.8+ and add to PATH
4. **Module not found**: Run pip install in virtual environment

## 🔄 Updates

### Server Updates
1. Stop the server/service
2. Replace files with new version
3. Run installation script again
4. Start the server/service

### Client Updates
1. Update JavaScript files in POS module
2. Clear browser cache
3. Restart Odoo/refresh POS

---

## 📋 Quick Reference

### URLs
- **Dashboard**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Global Objects
- **Logger**: `window.geideaLogger`
- **Session Info**: `window.geideaLogger.getSessionInfo()`

### Key Files
- **Server**: `main.py`
- **Client**: `logging_client.js`
- **Database**: `pos_geidea_logs.db`

### Service Names
- **Windows**: `PosGeideaLogging`
- **Linux**: `pos-geidea-logging`
- **macOS**: `com.pos.geidea.logging`