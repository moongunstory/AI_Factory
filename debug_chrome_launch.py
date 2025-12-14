from playwright.sync_api import sync_playwright
import time
from pathlib import Path

# Use system default profile
AUTOMATION_PROFILE = Path(r"C:\Users\moong\AppData\Local\Google\Chrome\User Data")
CHROME_EXECUTABLE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def test_launch():
    print("Testing Chrome Launch...")
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(AUTOMATION_PROFILE),
                executable_path=CHROME_EXECUTABLE,
                headless=False,
                args=[
                    "--profile-directory=Default",
                    "--no-sandbox",
                    "--disable-infobars",
                ],
                no_viewport=True,
                # ignore_default_args=["--enable-automation"], # Commented out to test connectivity
            )
            print("✅ Chrome launched successfully!")
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto("https://chatgpt.com")
            print("✅ Navigated to ChatGPT")
            
            time.sleep(5)
            browser.close()
            print("✅ Browser closed cleanly")
            
        except Exception as e:
            print(f"❌ Failed to launch: {e}")

if __name__ == "__main__":
    test_launch()
