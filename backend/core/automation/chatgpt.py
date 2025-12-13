import os
import time
import asyncio
from playwright.async_api import async_playwright, Page, BrowserContext

class ChatGPTClient:
    def __init__(self, user_data_dir: str = "chrome_profile"):
        self.user_data_dir = os.path.abspath(user_data_dir)
        self.target_url = "https://chatgpt.com/g/g-mBqCBRe17-fable-forge"
        self.browser_context: BrowserContext = None
        self.page: Page = None
        self.playwright = None

    async def start_browser(self):
        """
        Starts the browser with a persistent context.
        This allows cookies/login limits to be saved.
        """
        if self.page and not self.page.is_closed():
            return

        self.playwright = await async_playwright().start()
        
        # Launch options for stability and stealth
        self.browser_context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=False,  # Headed mode so user can see/login
            channel="chrome", # Use installed Chrome if available for better realism
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
            viewport={"width": 1280, "height": 800}
        )
        
        # Get the first page or create new one
        if self.browser_context.pages:
            self.page = self.browser_context.pages[0]
        else:
            self.page = await self.browser_context.new_page()

    async def ensure_on_target_page(self):
        """Navigates to the Fable Forge GPT if not already there."""
        if self.page.url != self.target_url:
            await self.page.goto(self.target_url)
            # Wait for potential redirects or loading
            await self.page.wait_for_load_state("networkidle")

    async def send_message_and_get_response(self, text: str):
        """
        Types the text, sends it, waits for generation, and returns the response.
        """
        if not self.page:
            await self.start_browser()
        
        await self.ensure_on_target_page()

        # Check if we are logged in by looking for the textarea
        try:
            # Common selector for the prompting area
            textarea_selector = "#prompt-textarea"
            await self.page.wait_for_selector(textarea_selector, timeout=5000)
        except:
            # If textarea not found, we might be at login screen
            raise Exception("Input area not found. Please log in to ChatGPT in the opened browser window.")

        # Type the message
        # Using sequential typing to look more human
        await self.page.click(textarea_selector)
        await self.page.fill(textarea_selector, text)
        
        # Give a small pause
        await asyncio.sleep(0.5)

        # Send (Enter key is usually safest)
        await self.page.keyboard.press("Enter")

        # === WAIT FOR GENERATION ===
        # Strategy: Wait for the "Stop generating" button to appear, then disappear.
        # But for short messages, it might appear/disappear too fast.
        # Better Strategy: Wait for the result streaming to finish.
        
        print("Waiting for response generation...")
        
        # Wait a bit for the request to process
        await asyncio.sleep(2)
        
        # Wait for the "Stop generating" button to vanish (indicating done)
        # The selector for stop button often has aria-label="Stop generating" or specific class
        # Current method: Check for specific "assistant" message bubbles update.
        
        # We'll use a simple polling mechanism to see if the "streaming" class is gone from the last message
        # or wait for a specific 'copy' button to appear on the last message
        
        # Let's wait for network idle again as a heuristic
        await self.page.wait_for_load_state("networkidle")
        
        # Additional safety wait (generation takes time)
        # A more robust way: Count the number of assistant messages, find the last one, and wait for it to stabilize.
        
        # For now, let's wait for a generous amount of time or until specific markers (like the copy button) appear
        # The 'Copy' button usually appears after generation is complete.
        try:
            # This selector targets the copy button at the bottom of a message
            # It might need adjustment if ChatGPT UI changes, but it's a good proxy for "Done"
            await self.page.wait_for_selector('button[aria-label="Copy"]', state="attached", timeout=60000)
        except:
            print("Warning: Copy button wait timed out, but continuing...")

        # === EXTRACT LAST RESPONSE ===
        # Select all assistant responses
        assistant_msgs = self.page.locator('div[data-message-author-role="assistant"]')
        count = await assistant_msgs.count()
        
        if count == 0:
            return "Error: No response found."
            
        last_msg = assistant_msgs.nth(count - 1)
        
        # Get the text content
        response_text = await last_msg.inner_text()
        return response_text

    async def close(self):
        if self.browser_context:
            await self.browser_context.close()
