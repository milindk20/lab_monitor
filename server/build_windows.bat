@echo off
echo Building LabMonitor Server for Windows...
echo.

pip install pyinstaller flask requests

pyinstaller --onefile --noconsole --name LabMonitorServer --add-data "templates;templates" app.py

echo.
echo Build complete! EXE is in dist\LabMonitorServer.exe
echo.
pause
