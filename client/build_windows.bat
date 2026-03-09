@echo off
echo Building LabMonitor Client for Windows...
echo.

pip install pyinstaller mss requests

pyinstaller --onefile --noconsole --name LabMonitor --add-data "config.json;." capture.py

echo.
echo Build complete! EXE is in dist\LabMonitor.exe
echo.
pause
