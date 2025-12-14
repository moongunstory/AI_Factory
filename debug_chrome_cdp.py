import subprocess
import time
from playwright.sync_api import sync_playwright
from pathlib import Path

# Config
CHROME_EXECUTABLE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = r"C:\Users\moong\AppData\Local\Google\Chrome\User Data"
PORT = 9222

def test_cdp():
    print("🚀 Launching Chrome via Subprocess...")
    
    cmd = [
        CHROME_EXECUTABLE,
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "--profile-directory=Default",
        "--no-sandbox",
        "--disable-infobars"
    ]
    
    # Launch Chrome
    proc = subprocess.Popen(cmd)
    
    print(f"✅ Chrome launched (PID: {proc.pid}). Waiting for CDP...")
    time.sleep(3)
    
    try:
        with sync_playwright() as p:
            print(f"🔗 Connecting to CDP on port {PORT}...")
            browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
            print("✅ Connected to Chrome!")
            
            ctx = browser.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            
            print(f"📄 Current Title: {page.title()}")
            page.goto("https://chatgpt.com")
            print("✅ Navigated to ChatGPT")
            
            # Keep open for a moment
            time.sleep(5)
            
            print("Disconnecting...")
            browser.close() # This just disconnects usually
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("Killing Chrome process...")
        proc.kill()

if __name__ == "__main__":
    test_cdp()
