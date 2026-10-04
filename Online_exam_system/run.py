"""
One-Click Launcher for Online Exam & Quiz System
Starts Flask and automatically opens your web browser.
"""

import webbrowser
import threading
import time
from app import app, init_db

def open_browser():
    # Wait 1.5 seconds for Flask server to initialize
    time.sleep(1.5)
    url = "http://127.0.0.1:5001"
    print("\n" + "="*60)
    print(f"🚀 Browser me website kholi ja rahi hai: {url}")
    print("="*60 + "\n")
    webbrowser.open(url)

if __name__ == '__main__':
    init_db()
    # Start browser opener in background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("\n" + "="*60)
    print("🎓 ONLINE EXAM & QUIZ SYSTEM START HO GAYA HAI!")
    print("👉 PC Website URL: http://127.0.0.1:5001")
    print("👉 Mobile URL:     http://10.131.240.31:5001")
    print("⚠️  DHYAN DEIN: Is black window (terminal) ko band MAT kijiye ga.")
    print("    Jab tak ye window open rahegi, tab tak website chalegi.")
    print("="*60 + "\n")
    
    # Run server
    app.run(host='0.0.0.0', port=5001, debug=False)
