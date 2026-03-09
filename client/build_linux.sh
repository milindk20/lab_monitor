#!/bin/bash
echo "Building LabMonitor Client for Linux..."
echo

pip install pyinstaller mss requests

pyinstaller --onefile --name LabMonitor --add-data "config.json:." capture.py

echo
echo "Build complete! Binary is in dist/LabMonitor"
echo
