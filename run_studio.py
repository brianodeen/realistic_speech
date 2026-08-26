"""
Launcher script for Universal Phonetic Speech Studio.
Starts FastAPI backend server and opens the studio UI in the default browser.
"""

import sys
import webbrowser
import threading
import time
import uvicorn


def open_browser():
    time.sleep(1.2)
    url = "http://127.0.0.1:8000"
    print(f"\n[+] Opening Universal Phonetic Speech Studio at {url}")
    webbrowser.open(url)


def main():
    print("=" * 65)
    print("   UNIVERSAL PHONETIC SPEECH STUDIO")
    print("   Conlangs • Animal Vocalizations • Micro-Prosody & Chao Tones")
    print("=" * 65)
    print("\nStarting local FastAPI synthesis server...")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run uvicorn server
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
