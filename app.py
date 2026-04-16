import psutil
import threading
import time
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
blocked_paths = set()
blocked_names = set()

def normalize(p):
    return os.path.normpath(p.strip().replace('"', '')).lower()

def monitor_processes():
    while True:
        for proc in psutil.process_iter(['exe', 'name']):
            try:
                exe_path = proc.info.get('exe')
                exe_name = proc.info.get('name')
                if exe_path and normalize(exe_path) in blocked_paths:
                    proc.kill()
                elif exe_name and exe_name.lower() in blocked_names:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        time.sleep(0.3)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sync', methods=['POST'])
def sync():
    global blocked_paths, blocked_names
    data = request.json
    raw_paths = data.get('paths', [])
    blocked_paths.clear()
    blocked_names.clear()
    for p in raw_paths:
        if p:
            norm_p = normalize(p)
            blocked_paths.add(norm_p)
            blocked_names.add(os.path.basename(norm_p))
    return jsonify({"status": "success"})

if __name__ == '__main__':
    threading.Thread(target=monitor_processes, daemon=True).start()
    app.run(port=5000)