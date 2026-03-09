# Lab Monitor - Screen Monitoring System

Real-time screen monitoring system for lab environments. Captures screenshots every 2 seconds from multiple Windows machines and displays them on a web dashboard.

## Architecture

```
[Lab PCs] --2s--> [Server:9990] --> [Web Dashboard]
                         |
                    screenshots/
                    └── {machine_name}/
```

## Components

### Server (`server/`)
- Flask web server
- Receives screenshots via HTTP POST
- Serves web dashboard with live grid view
- Auto-refreshes every 2 seconds

### Client (`client/`)
- Runs on each lab machine
- Captures full screen every 2 seconds
- Sends to server via HTTP
- Runs as hidden background process
- Auto-starts on Windows boot

---

## Setup

### 1. Server Setup (on "quick sequrite" machine)

**Install dependencies:**
```cmd
pip install flask requests
```

**Start server:**
```cmd
python server\app.py
```

**Access dashboard:**
```
http://localhost:9990
```

### 2. Client Setup (on each lab machine)

**Build the client (run on the target OS):**

| OS | Build Command |
|----|---------------|
| Windows | `build_windows.bat` |
| Linux | `chmod +x build_linux.sh && ./build_linux.sh` |
| macOS | `chmod +x build_macos.sh && ./build_macos.sh` |

**Configure client (after building):**
Edit `dist/config.json`:
```json
{
    "server_url": "http://192.168.29.74:9990",
    "custom_name": "lab-pc-01",
    "capture_interval": 2,
    "auto_start": true
}
```

**Deploy:**
1. Copy the binary AND `config.json` to each lab machine
2. Run the client - it will:
   - Read config from config.json
   - Start capturing screenshots
   - Add itself to OS startup

The EXE will be at `client\dist\LabMonitor.exe`

**Deploy:**
1. Copy `LabMonitor.exe` to each lab machine
2. Run once - it will:
   - Start capturing screenshots
   - Add itself to Windows startup (auto-run on boot)
3. The EXE runs hidden (no window, no tray icon)

---

## QuickHeal/Firewall Configuration

### If QuickHeal blocks the client:
1. Open QuickHeal Total Security
2. Go to **Settings** > **Virus Protection** > **Exclusions**
3. Add `LabMonitor.exe` to exclusions

### If Windows Firewall blocks:
1. Allow the client through firewall when prompted, OR
2. Run as Administrator first time

### Server firewall (if needed):
```cmd
netsh advfirewall firewall add rule name="LabMonitor" dir=in action=allow protocol=tcp localport=9990
```

---

## Usage

### Start Server
```cmd
cd server
python app.py
```

### Access Dashboard
Open browser: `http://<server-ip>:9990`

The dashboard shows:
- All connected machines in a grid
- Latest screenshot from each machine
- Auto-refresh every 2 seconds
- Last seen timestamp

---

## Configuration Options

### config.json

| Option | Description | Default |
|--------|-------------|---------|
| `server_url` | Server URL (IP:port) | `http://192.168.29.74:9990` |
| `capture_interval` | Seconds between captures | `2` |
| `custom_name` | Custom machine name (optional) | `""` (uses IP) |
| `auto_start` | Add to Windows startup | `true` |

### server/app.py (Housekeeping)

To enable automatic cleanup of old screenshots (default: disabled):

```python
# Line ~140 in app.py
cleanup_old_screenshots(days=30, enabled=True)  # Change to True
```

---

## File Structure

```
lab-monitor/
├── README.md                    # Full documentation
├── server/
│   ├── app.py                   # Flask server
│   ├── requirements.txt
│   └── templates/
│       └── index.html           # Web dashboard
└── client/
    ├── capture.py               # Screenshot client (cross-platform)
    ├── config.json              # Configuration template
    ├── requirements.txt
    ├── build_windows.bat        # Build for Windows
    ├── build_linux.sh           # Build for Linux
    └── build_macos.sh           # Build for macOS
```

## Deploy Binary + Config

Build on target OS, then deploy:

```
dist/
├── LabMonitor         # Linux/macOS
OR
LabMonitor.exe        # Windows
+
config.json           # Edit this per machine
```
lab-monitor/
├── server/
│   ├── app.py              # Flask server
│   ├── templates/
│   │   └── index.html      # Web dashboard
│   └── screenshots/        # Auto-created, stores images
│       └── {machine_name}/
│           └── {timestamp}_{ip}.jpg
├── client/
│   ├── capture.py          # Screenshot client
│   ├── config.py          # Configuration
│   └── build_client.bat   # Build script
└── README.md
```

---

## Troubleshooting

**Client not connecting:**
- Check SERVER_URL is correct
- Verify network connectivity: `ping <server-ip>`
- Check QuickHeal/firewall exclusions

**Server not receiving screenshots:**
- Verify port 9990 is open
- Check server console for errors

**No screenshots showing:**
- Wait ~5 seconds for first capture
- Check `server/screenshots/` folder for images
- Check browser console for JS errors

---

## Security Notes

- No authentication on web interface (as requested)
- Screenshots are stored unencrypted
- Client runs with user privileges only
- Suitable for internal lab use only
