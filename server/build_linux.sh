#!/bin/bash
echo "Building LabMonitor Server for Linux..."
echo

pip install pyinstaller flask requests

pyinstaller --onefile --name LabMonitorServer --add-data "templates:templates" app.py

echo
echo "Build complete! Binary is in dist/LabMonitorServer"
echo
