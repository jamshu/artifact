#!/usr/bin/env python3
"""
POS Geidea Logging Server
FastAPI server to collect and store POS debugging logs in SQLite database
"""

import asyncio
import sqlite3
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Configuration
DB_FILE = "pos_geidea_logs.db"
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Pydantic models
class LogEntry(BaseModel):
    session_id: str = Field(..., description="POS session identifier")
    order_id: Optional[str] = Field(None, description="Current order ID")
    user_id: Optional[str] = Field(None, description="User ID")
    component: str = Field(..., description="Component name (payment, restriction, etc.)")
    level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")
    message: str = Field(..., description="Log message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional structured data")
    timestamp: Optional[datetime] = Field(None, description="Client timestamp")
    url: Optional[str] = Field(None, description="Browser URL")
    user_agent: Optional[str] = Field(None, description="Browser user agent")

class LogQuery(BaseModel):
    session_id: Optional[str] = None
    component: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

# FastAPI app
app = FastAPI(
    title="POS Geidea Logging Server",
    description="Local logging server for POS Geidea payment terminal debugging",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_id TEXT UNIQUE NOT NULL,
            session_id TEXT NOT NULL,
            order_id TEXT,
            user_id TEXT,
            component TEXT NOT NULL,
            level TEXT NOT NULL DEFAULT 'INFO',
            message TEXT NOT NULL,
            data TEXT,  -- JSON string
            timestamp DATETIME,
            server_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            url TEXT,
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indices for better query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON pos_logs(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_component ON pos_logs(component)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_level ON pos_logs(level)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON pos_logs(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_server_timestamp ON pos_logs(server_timestamp)")
    
    # Create sessions table for session tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_agent TEXT,
            status TEXT DEFAULT 'active'
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_FILE}")

async def store_log_entry(log_entry: LogEntry):
    """Store log entry in database asynchronously"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        log_id = str(uuid.uuid4())
        server_timestamp = datetime.now(timezone.utc)
        
        # Convert data to JSON string if present
        data_json = json.dumps(log_entry.data) if log_entry.data else None
        
        cursor.execute("""
            INSERT INTO pos_logs (
                log_id, session_id, order_id, user_id, component, level, 
                message, data, timestamp, server_timestamp, url, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_id, log_entry.session_id, log_entry.order_id, log_entry.user_id,
            log_entry.component, log_entry.level, log_entry.message, data_json,
            log_entry.timestamp or server_timestamp, server_timestamp,
            log_entry.url, log_entry.user_agent
        ))
        
        # Update session activity
        cursor.execute("""
            INSERT OR REPLACE INTO pos_sessions (
                session_id, user_id, last_activity, user_agent, status
            ) VALUES (?, ?, ?, ?, 'active')
        """, (log_entry.session_id, log_entry.user_id, server_timestamp, log_entry.user_agent))
        
        conn.commit()
        conn.close()
        
        print(f"📝 Logged: [{log_entry.level}] {log_entry.component}: {log_entry.message[:100]}...")
        
    except Exception as e:
        print(f"❌ Error storing log: {e}")
        # Store to backup file if database fails
        backup_file = LOG_DIR / f"backup_{datetime.now().strftime('%Y%m%d')}.log"
        with open(backup_file, "a") as f:
            f.write(f"{server_timestamp.isoformat()} | ERROR | {e} | {log_entry.json()}\n")

# API Routes
@app.post("/api/logs", status_code=201)
async def create_log(log_entry: LogEntry, background_tasks: BackgroundTasks):
    """Create a new log entry"""
    background_tasks.add_task(store_log_entry, log_entry)
    return {"status": "accepted", "message": "Log entry queued for processing"}

@app.post("/api/logs/batch", status_code=201)
async def create_logs_batch(log_entries: List[LogEntry], background_tasks: BackgroundTasks):
    """Create multiple log entries in batch"""
    for log_entry in log_entries:
        background_tasks.add_task(store_log_entry, log_entry)
    return {"status": "accepted", "message": f"{len(log_entries)} log entries queued for processing"}

@app.get("/api/logs")
async def get_logs(
    session_id: Optional[str] = None,
    component: Optional[str] = None,
    level: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Retrieve logs with filtering options"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM pos_logs WHERE 1=1"
        params = []
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        if component:
            query += " AND component = ?"
            params.append(component)
            
        if level:
            query += " AND level = ?"
            params.append(level)
            
        if start_time:
            query += " AND server_timestamp >= ?"
            params.append(start_time)
            
        if end_time:
            query += " AND server_timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY server_timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionaries
        columns = [description[0] for description in cursor.description]
        logs = []
        for row in rows:
            log_dict = dict(zip(columns, row))
            # Parse JSON data if present
            if log_dict['data']:
                try:
                    log_dict['data'] = json.loads(log_dict['data'])
                except:
                    pass
            logs.append(log_dict)
        
        conn.close()
        return {"logs": logs, "count": len(logs), "limit": limit, "offset": offset}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/api/sessions")
async def get_sessions():
    """Get all active sessions"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pos_sessions ORDER BY last_activity DESC")
        rows = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description]
        sessions = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return {"sessions": sessions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/api/stats")
async def get_stats():
    """Get logging statistics"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get counts by component
        cursor.execute("SELECT component, COUNT(*) as count FROM pos_logs GROUP BY component")
        components = dict(cursor.fetchall())
        
        # Get counts by level
        cursor.execute("SELECT level, COUNT(*) as count FROM pos_logs GROUP BY level")
        levels = dict(cursor.fetchall())
        
        # Get total logs
        cursor.execute("SELECT COUNT(*) FROM pos_logs")
        total_logs = cursor.fetchone()[0]
        
        # Get active sessions
        cursor.execute("SELECT COUNT(*) FROM pos_sessions WHERE status = 'active'")
        active_sessions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_logs": total_logs,
            "active_sessions": active_sessions,
            "by_component": components,
            "by_level": levels
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.delete("/api/logs")
async def clear_logs(older_than_days: Optional[int] = None):
    """Clear logs (optionally older than specified days)"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        if older_than_days:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
            cursor.execute("DELETE FROM pos_logs WHERE server_timestamp < ?", (cutoff_date,))
            message = f"Cleared logs older than {older_than_days} days"
        else:
            cursor.execute("DELETE FROM pos_logs")
            cursor.execute("DELETE FROM pos_sessions")
            message = "Cleared all logs and sessions"
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return {"message": message, "deleted_count": deleted_count}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/api/export/{session_id}")
async def export_session_logs(session_id: str):
    """Export logs for a specific session as JSON"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pos_logs WHERE session_id = ? ORDER BY server_timestamp", (session_id,))
        rows = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description]
        logs = []
        for row in rows:
            log_dict = dict(zip(columns, row))
            if log_dict['data']:
                try:
                    log_dict['data'] = json.loads(log_dict['data'])
                except:
                    pass
            logs.append(log_dict)
        
        conn.close()
        
        # Save to file
        export_file = LOG_DIR / f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w') as f:
            json.dump(logs, f, indent=2, default=str)
        
        return FileResponse(export_file, filename=export_file.name)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {e}")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Simple dashboard for viewing logs"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>POS Geidea Logging Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
            .stats { display: flex; gap: 20px; margin-bottom: 20px; }
            .stat-card { background: #e8f4fd; padding: 15px; border-radius: 5px; flex: 1; }
            .logs { background: #f9f9f9; padding: 20px; border-radius: 5px; }
            .log-entry { margin-bottom: 10px; padding: 10px; background: white; border-radius: 3px; }
            .log-level-ERROR { border-left: 4px solid #ff4444; }
            .log-level-WARNING { border-left: 4px solid #ffaa00; }
            .log-level-INFO { border-left: 4px solid #0088ff; }
            .log-level-DEBUG { border-left: 4px solid #888888; }
            button { background: #0088ff; color: white; border: none; padding: 10px 20px; border-radius: 3px; cursor: pointer; }
            button:hover { background: #0066cc; }
            input, select { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔧 POS Geidea Logging Dashboard</h1>
            <p>Real-time debugging logs for POS Geidea payment terminal</p>
        </div>
        
        <div id="stats" class="stats"></div>
        
        <div class="logs">
            <h2>Recent Logs</h2>
            <div>
                <input type="text" id="sessionFilter" placeholder="Session ID">
                <select id="componentFilter">
                    <option value="">All Components</option>
                    <option value="payment">Payment</option>
                    <option value="restriction">Restriction</option>
                    <option value="terminal">Terminal</option>
                </select>
                <select id="levelFilter">
                    <option value="">All Levels</option>
                    <option value="ERROR">Error</option>
                    <option value="WARNING">Warning</option>
                    <option value="INFO">Info</option>
                    <option value="DEBUG">Debug</option>
                </select>
                <button onclick="refreshLogs()">Refresh</button>
                <button onclick="clearLogs()">Clear All</button>
            </div>
            <div id="logs-container"></div>
        </div>

        <script>
            async function loadStats() {
                try {
                    const response = await fetch('/api/stats');
                    const stats = await response.json();
                    
                    document.getElementById('stats').innerHTML = `
                        <div class="stat-card">
                            <h3>Total Logs</h3>
                            <p style="font-size: 24px; margin: 0;">${stats.total_logs}</p>
                        </div>
                        <div class="stat-card">
                            <h3>Active Sessions</h3>
                            <p style="font-size: 24px; margin: 0;">${stats.active_sessions}</p>
                        </div>
                        <div class="stat-card">
                            <h3>Components</h3>
                            <p>${Object.keys(stats.by_component).join(', ')}</p>
                        </div>
                        <div class="stat-card">
                            <h3>Error Count</h3>
                            <p style="font-size: 24px; margin: 0; color: #ff4444;">${stats.by_level.ERROR || 0}</p>
                        </div>
                    `;
                } catch (error) {
                    console.error('Failed to load stats:', error);
                }
            }
            
            async function refreshLogs() {
                try {
                    const sessionId = document.getElementById('sessionFilter').value;
                    const component = document.getElementById('componentFilter').value;
                    const level = document.getElementById('levelFilter').value;
                    
                    const params = new URLSearchParams();
                    if (sessionId) params.append('session_id', sessionId);
                    if (component) params.append('component', component);
                    if (level) params.append('level', level);
                    params.append('limit', '50');
                    
                    const response = await fetch(`/api/logs?${params}`);
                    const data = await response.json();
                    
                    const logsHtml = data.logs.map(log => `
                        <div class="log-entry log-level-${log.level}">
                            <strong>[${log.level}]</strong> 
                            <span style="color: #666;">${new Date(log.server_timestamp).toLocaleString()}</span>
                            <span style="color: #0066cc;">${log.component}</span><br>
                            <strong>Session:</strong> ${log.session_id}<br>
                            <strong>Message:</strong> ${log.message}<br>
                            ${log.data ? `<strong>Data:</strong> <pre style="background: #f0f0f0; padding: 5px; border-radius: 3px; font-size: 12px; overflow-x: auto;">${JSON.stringify(log.data, null, 2)}</pre>` : ''}
                        </div>
                    `).join('');
                    
                    document.getElementById('logs-container').innerHTML = logsHtml || '<p>No logs found</p>';
                } catch (error) {
                    console.error('Failed to load logs:', error);
                    document.getElementById('logs-container').innerHTML = '<p>Error loading logs</p>';
                }
            }
            
            async function clearLogs() {
                if (confirm('Are you sure you want to clear all logs?')) {
                    try {
                        await fetch('/api/logs', { method: 'DELETE' });
                        alert('All logs cleared');
                        refreshLogs();
                        loadStats();
                    } catch (error) {
                        console.error('Failed to clear logs:', error);
                        alert('Error clearing logs');
                    }
                }
            }
            
            // Auto-refresh every 10 seconds
            setInterval(() => {
                refreshLogs();
                loadStats();
            }, 10000);
            
            // Initial load
            loadStats();
            refreshLogs();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected" if os.path.exists(DB_FILE) else "not_found"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    print("🚀 POS Geidea Logging Server started")
    print(f"📊 Dashboard: http://localhost:8000/")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"💾 Database: {DB_FILE}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )