"""
Desktop App Launcher for Online Exam & Quiz System
Launches the system as a dedicated, standalone Desktop Application window (No browser address bar).
"""

import subprocess
import threading
import time
import os
from app import app, init_db

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def launch_app_window():
    time.sleep(1.5)
    url = "http://127.0.0.1:5001"
    
    # Prefer Chrome, fallback to Edge
    browser_exe = CHROME_PATH if os.path.exists(CHROME_PATH) else EDGE_PATH
    
    print("\n" + "="*60)
    print("🚀 DESKTOP APP WINDOW OPEN KIYA JA RAHA HAI...")
    print("="*60 + "\n")
    
    # Launch in standalone App Mode
    subprocess.Popen([browser_exe, f"--app={url}", "--window-size=1200,800"])

if __name__ == '__main__':
    init_db()
    
    # Start app window in background thread
    threading.Thread(target=launch_app_window, daemon=True).start()
    
    print("\n" + "="*60)
    print("🎓 EXAM PORTAL DESKTOP APP RUNNING!")
    print("👉 PC: http://127.0.0.1:5001")
    print("👉 Mobile: http://10.131.240.31:5001")
    print("⚠️  Is console window ko minimize karke rakh sakte hain.")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
