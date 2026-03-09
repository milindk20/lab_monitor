import os
import time
import json
from datetime import datetime, timedelta
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), 'screenshots')
UPLOAD_FOLDER = SCREENSHOT_DIR
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

machine_last_seen = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_machine_folder(machine_id):
    safe_id = secure_filename(machine_id)
    folder = os.path.join(SCREENSHOT_DIR, safe_id)
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder, safe_id

def cleanup_old_screenshots(days=30, enabled=False):
    if not enabled:
        return
    
    cutoff = time.time() - (days * 86400)
    for machine_folder in os.listdir(SCREENSHOT_DIR):
        machine_path = os.path.join(SCREENSHOT_DIR, machine_folder)
        if not os.path.isdir(machine_path):
            continue
        for filename in os.listdir(machine_path):
            filepath = os.path.join(machine_path, filename)
            if os.path.isfile(filepath):
                if os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)

@app.route('/')
def index():
    machines = []
    if os.path.exists(SCREENSHOT_DIR):
        for machine_folder in os.listdir(SCREENSHOT_DIR):
            machine_path = os.path.join(SCREENSHOT_DIR, machine_folder)
            if not os.path.isdir(machine_path):
                continue
            
            latest_image = None
            latest_time = 0
            for filename in os.listdir(machine_path):
                filepath = os.path.join(machine_path, filename)
                if os.path.isfile(filepath):
                    mtime = os.path.getmtime(filepath)
                    if mtime > latest_time:
                        latest_time = mtime
                        latest_image = filename
            
            if latest_image:
                last_seen = machine_last_seen.get(machine_folder, 'Unknown')
                machines.append({
                    'name': machine_folder,
                    'latest_image': f'screenshots/{machine_folder}/{latest_image}',
                    'last_seen': last_seen
                })
    
    return render_template('index.html', machines=machines)

@app.route('/api/machines')
def api_machines():
    machines = []
    if os.path.exists(SCREENSHOT_DIR):
        for machine_folder in os.listdir(SCREENSHOT_DIR):
            machine_path = os.path.join(SCREENSHOT_DIR, machine_folder)
            if not os.path.isdir(machine_path):
                continue
            
            latest_image = None
            latest_time = 0
            for filename in os.listdir(machine_path):
                filepath = os.path.join(machine_path, filename)
                if os.path.isfile(filepath):
                    mtime = os.path.getmtime(filepath)
                    if mtime > latest_time:
                        latest_time = mtime
                        latest_image = filename
            
            if latest_image:
                last_seen = machine_last_seen.get(machine_folder, 'Unknown')
                machines.append({
                    'name': machine_folder,
                    'latest_image': f'screenshots/{machine_folder}/{latest_image}',
                    'last_seen': last_seen
                })
    
    return jsonify(machines)

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        custom_name = request.form.get('custom_name', '').strip()
        ip_addr = request.form.get('ip', 'unknown')
        hostname = request.form.get('hostname', 'unknown')
        timestamp = request.form.get('timestamp', str(int(time.time())))
        
        if custom_name:
            machine_id = custom_name
        else:
            machine_id = ip_addr
        
        folder, safe_id = get_machine_folder(machine_id)
        machine_last_seen[safe_id] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        filename = file.filename or 'screenshot.jpg'
        ext = 'jpg'
        if '.' in filename:
            ext = filename.rsplit('.', 1)[1].lower()
        final_filename = f'{timestamp}_{ip_addr}.{ext}'
        filepath = os.path.join(folder, final_filename)
        file.save(filepath)
        
        return jsonify({'status': 'ok', 'machine': safe_id, 'file': final_filename}), 200
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/screenshots/<path:filename>')
def serve_screenshot(filename):
    from flask import send_from_directory
    return send_from_directory(SCREENSHOT_DIR, filename)

if __name__ == '__main__':
    cleanup_old_screenshots(days=30, enabled=False)
    print(f"[{datetime.now()}] Starting Lab Monitor Server on http://0.0.0.0:9990")
    print(f"[{datetime.now()}] Screenshots directory: {SCREENSHOT_DIR}")
    app.run(host='0.0.0.0', port=9990, debug=False, threaded=True)
