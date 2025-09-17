@echo off
:: POS Geidea Logging Server - Windows Installation Script
:: Run this script as Administrator for best results

echo ========================================
echo POS Geidea Logging Server Installation
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo ✅ Python found:
python --version

:: Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not available
    echo Please reinstall Python with pip included
    pause
    exit /b 1
)

echo ✅ pip found:
pip --version

:: Create virtual environment
echo.
echo 📦 Creating virtual environment...
if exist "venv" (
    echo Virtual environment already exists, removing old one...
    rmdir /s /q venv
)

python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

:: Activate virtual environment
echo.
echo ⚡ Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies
echo.
echo 📥 Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ✅ Installation completed successfully!
echo.

:: Create startup script
echo 🚀 Creating startup scripts...
echo @echo off > start_server.bat
echo call venv\Scripts\activate.bat >> start_server.bat
echo echo Starting POS Geidea Logging Server... >> start_server.bat
echo echo Dashboard: http://localhost:8000/ >> start_server.bat
echo echo API Docs: http://localhost:8000/docs >> start_server.bat
echo echo Press Ctrl+C to stop the server >> start_server.bat
echo echo. >> start_server.bat
echo python main.py >> start_server.bat
echo pause >> start_server.bat

:: Create service installation script
echo @echo off > install_service.bat
echo :: Run as Administrator to install as Windows Service >> install_service.bat
echo net session ^>nul 2^>^&1 >> install_service.bat
echo if %%errorLevel%% neq 0 ( >> install_service.bat
echo     echo This script must be run as Administrator >> install_service.bat
echo     pause >> install_service.bat
echo     exit /b 1 >> install_service.bat
echo ^) >> install_service.bat
echo. >> install_service.bat
echo echo Installing POS Geidea Logging Server as Windows Service... >> install_service.bat
echo pip install pywin32 >> install_service.bat
echo pip install pywin32-ctypes >> install_service.bat
echo. >> install_service.bat
echo :: Create service wrapper >> install_service.bat
echo ^(echo import sys >> service.py >> install_service.bat
echo echo import os >> service.py >> install_service.bat
echo echo import servicemanager >> service.py >> install_service.bat
echo echo import win32serviceutil >> service.py >> install_service.bat
echo echo import win32service >> service.py >> install_service.bat
echo echo import win32event >> service.py >> install_service.bat
echo echo import subprocess >> service.py >> install_service.bat
echo echo. >> service.py >> install_service.bat
echo echo class PosGeideaLoggingService^(win32serviceutil.ServiceFramework^): >> service.py >> install_service.bat
echo echo     _svc_name_ = "PosGeideaLogging" >> service.py >> install_service.bat
echo echo     _svc_display_name_ = "POS Geidea Logging Server" >> service.py >> install_service.bat
echo echo     _svc_description_ = "Local logging server for POS Geidea debugging" >> service.py >> install_service.bat
echo echo. >> service.py >> install_service.bat
echo echo     def __init__^(self, args^): >> service.py >> install_service.bat
echo echo         win32serviceutil.ServiceFramework.__init__^(self, args^) >> service.py >> install_service.bat
echo echo         self.hWaitStop = win32event.CreateEvent^(None, 0, 0, None^) >> service.py >> install_service.bat
echo echo         self.process = None >> service.py >> install_service.bat
echo echo. >> service.py >> install_service.bat
echo echo     def SvcStop^(self^): >> service.py >> install_service.bat
echo echo         self.ReportServiceStatus^(win32service.SERVICE_STOP_PENDING^) >> service.py >> install_service.bat
echo echo         if self.process: >> service.py >> install_service.bat
echo echo             self.process.terminate^(^) >> service.py >> install_service.bat
echo echo         win32event.SetEvent^(self.hWaitStop^) >> service.py >> install_service.bat
echo echo. >> service.py >> install_service.bat
echo echo     def SvcDoRun^(self^): >> service.py >> install_service.bat
echo echo         import os >> service.py >> install_service.bat
echo echo         os.chdir^(r'%CD%'^) >> service.py >> install_service.bat
echo echo         self.process = subprocess.Popen^([r'%CD%\venv\Scripts\python.exe', r'%CD%\main.py']^) >> service.py >> install_service.bat
echo echo         win32event.WaitForSingleObject^(self.hWaitStop, win32event.INFINITE^) >> service.py >> install_service.bat
echo echo. >> service.py >> install_service.bat
echo echo if __name__ == '__main__': >> service.py >> install_service.bat
echo echo     win32serviceutil.HandleCommandLine^(PosGeideaLoggingService^) >> service.py^) >> install_service.bat
echo. >> install_service.bat
echo python service.py install >> install_service.bat
echo python service.py start >> install_service.bat
echo echo. >> install_service.bat
echo echo ✅ Service installed and started! >> install_service.bat
echo echo The logging server will now start automatically with Windows. >> install_service.bat
echo pause >> install_service.bat

echo ✅ Created start_server.bat - Double-click to start the server
echo ✅ Created install_service.bat - Run as Admin to install as Windows service
echo.

:: Ask user if they want to start the server now
choice /M "Do you want to start the logging server now"
if %errorlevel% equ 1 (
    echo.
    echo 🚀 Starting POS Geidea Logging Server...
    echo Dashboard: http://localhost:8000/
    echo API Docs: http://localhost:8000/docs
    echo Press Ctrl+C to stop the server
    echo.
    python main.py
) else (
    echo.
    echo 📋 To start the server later, run: start_server.bat
    echo 📋 To install as Windows service, run install_service.bat as Administrator
)

echo.
echo Installation completed!
pause