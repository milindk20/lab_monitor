import os
import sys
import time
import socket
import json
import platform
import logging
from datetime import datetime

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found. Install with: pip install requests")
    sys.exit(1)

try:
    import mss
    import mss.tools
except ImportError:
    print("Error: 'mss' library not found. Install with: pip install mss")
    sys.exit(1)

def setup_logging():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    log_dir = os.path.join(base_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'labmonitor_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def get_config():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    config_path = os.path.join(base_path, 'config.json')
    
    defaults = {
        'server_url': 'http://192.168.29.74:9990',
        'capture_interval': 2,
        'custom_name': '',
        'auto_start': True,
        'headless': False
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return {**defaults, **config}
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return defaults
    return defaults

def get_machine_info():
    hostname = socket.gethostname()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "unknown"
    return hostname, ip

def add_to_startup():
    system = platform.system()
    exe_path = sys.executable
    
    if system == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "LabMonitor", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            logger.info("Added to Windows startup")
        except Exception as e:
            logger.warning(f"Failed to add to Windows startup: {e}")
    
    elif system == "Linux":
        autostart_dir = os.path.expanduser("~/.config/autostart")
        os.makedirs(autostart_dir, exist_ok=True)
        desktop_entry = os.path.join(autostart_dir, "LabMonitor.desktop")
        content = f"""[Desktop Entry]
Type=Application
Name=LabMonitor
Exec={exe_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
        try:
            with open(desktop_entry, 'w') as f:
                f.write(content)
            logger.info("Added to Linux autostart")
        except Exception as e:
            logger.warning(f"Failed to add to Linux autostart: {e}")
    
    elif system == "Darwin":
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.labmonitor.plist")
        content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.labmonitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
        try:
            os.makedirs(os.path.dirname(plist_path), exist_ok=True)
            with open(plist_path, 'w') as f:
                f.write(content)
            logger.info("Added to macOS LaunchAgents")
        except Exception as e:
            logger.warning(f"Failed to add to macOS autostart: {e}")

def check_display():
    system = platform.system()
    if system == "Linux":
        display = os.environ.get('DISPLAY')
        if not display:
            return False, "DISPLAY environment variable not set (no X server)"
        try:
            import subprocess
            result = subprocess.run(['xdpyinfo'], capture_output=True, timeout=5)
            if result.returncode != 0:
                return False, "X server not accessible (xdpyinfo failed)"
        except FileNotFoundError:
            return False, "xdpinfo not found - install x11-utils package"
        except Exception as e:
            return False, f"Cannot connect to X server: {e}"
    return True, "Display available"

def capture_and_send():
    hostname, ip = get_machine_info()
    config = get_config()
    
    server_url = config.get('server_url', 'http://192.168.29.74:9990')
    interval = config.get('capture_interval', 2)
    custom_name = config.get('custom_name', '')
    headless = config.get('headless', False)
    
    logger.info(f"Starting LabMonitor - Hostname: {hostname}, IP: {ip}, Server: {server_url}")
    logger.info(f"Capture interval: {interval}s, Custom name: {custom_name or 'none'}, Headless: {headless}")
    
    if headless:
        logger.warning("Running in HEADLESS mode - no screenshots will be captured")
        logger.warning("Set 'headless': false in config.json to enable capture")
        while True:
            time.sleep(interval)
    
    display_ok, display_msg = check_display()
    if not display_ok:
        logger.error(f"[ERROR] {display_msg}")
        logger.error("[ERROR] Cannot capture screenshot - no display available")
        logger.error("[ERROR] This machine has no display attached (headless server)")
        logger.error("[ERROR] Set 'headless': true in config.json to run without capture")
        
        if platform.system() == "Linux":
            logger.error("[ERROR] Or install: sudo apt-get install x11-utils")
        
        while True:
            time.sleep(interval)
    
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        
        while True:
            try:
                sct_img = sct.grab(monitor)
                img_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
                
                timestamp = int(time.time())
                
                files = {
                    'image': ('screenshot.jpg', img_bytes, 'image/jpeg')
                }
                data = {
                    'ip': ip,
                    'hostname': hostname,
                    'custom_name': custom_name,
                    'timestamp': str(timestamp)
                }
                
                try:
                    response = requests.post(
                        f"{server_url}/upload",
                        files=files,
                        data=data,
                        timeout=10
                    )
                    if response.status_code == 200:
                        logger.info(f"[SUCCESS] Screenshot sent - {hostname}/{ip} - {datetime.now().strftime('%H:%M:%S')}")
                    else:
                        logger.error(f"[FAILED] Server returned {response.status_code} - {hostname}/{ip}")
                except requests.exceptions.ConnectionError as e:
                    logger.error(f"[FAILED] Connection error - {hostname}/{ip} - {e}")
                except requests.exceptions.Timeout as e:
                    logger.error(f"[FAILED] Timeout - {hostname}/{ip} - {e}")
                except Exception as e:
                    logger.error(f"[FAILED] Unexpected error - {hostname}/{ip} - {e}")
                    
            except Exception as e:
                logger.error(f"[ERROR] Capture failed - {hostname}/{ip} - {e}")
            
            time.sleep(interval)

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("LabMonitor Client Starting")
    logger.info("=" * 50)
    
    config = get_config()
    
    if config.get('auto_start', True):
        add_to_startup()
    
    capture_and_send()
