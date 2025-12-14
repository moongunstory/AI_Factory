"""Robust ChatGPT Client - Smart Automation & System Profile Support"""
import os
import time
import random
import sys
from pathlib import Path
from typing import Optional, Dict

from playwright.sync_api import sync_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError, Locator

# --- Configuration ---
SYSTEM_CHROME_PROFILE = r"C:\Users\moong\AppData\Local\Google\Chrome\User Data"
CHROME_EXECUTABLE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_URL = "http://127.0.0.1:9222"  # IPv4 명시 (localhost는 IPv6로 해석될 수 있음)

class ChatGPTClient:
    """
    Robust, human-like automation for ChatGPT using the local System Chrome Profile.
    Implements a State Machine for response detection and avoids API-like behavior.
    """

    GPT_URLS = {
        "fable_forge": "https://chatgpt.com/g/g-mBqCBRe17-fable-forge",
        "storyboard_gpt": "https://chatgpt.com/g/g-fPCGX4kUc-storyboard-gpt",
        "storyboard_maker": "https://chatgpt.com/g/g-jtTGRSqZ9-storyboard-maker"
    }

    def __init__(self):
        self.playwright = None
        self.browser = None  # CDP browser instance
        self.context: BrowserContext = None
        self.page: Page = None
        self.user_data_dir = SYSTEM_CHROME_PROFILE

    def start_browser(self):
        """Starts the browser using System Profile (CDP first, then Launch)."""
        if self.page and not self.page.is_closed():
            return

        self.playwright = sync_playwright().start()

        # 1. Try CDP (Preferred: Connect to running Chrome)
        try:
            print(f"[Worker] Connecting to Chrome via CDP ({CDP_URL})...")
            self.browser = self.playwright.chromium.connect_over_cdp(CDP_URL)
            if self.browser.contexts:
                self.context = self.browser.contexts[0]
            else:
                self.context = self.browser.new_context()
            
            # Setup Page
            if self.context.pages:
                self.page = self.context.pages[0]
                self.page.bring_to_front()
            else:
                self.page = self.context.new_page()
            
            print("[Worker] ✅ Connected to existing Chrome session.")
            return

        except Exception as e:
            print(f"[Worker] CDP connection failed: {e}")
            print("\n" + "="*60)
            print("⚠️  Chrome Debug Mode가 필요합니다!")
            print("="*60)
            print("AI Factory는 System Chrome Profile을 사용하기 위해")
            print("수동으로 시작된 Chrome Debug 세션에 연결해야 합니다.")
            print()
            print("해결 방법:")
            print("1. 프로젝트 루트의 'start_chrome_debug.bat' 실행")
            print("2. Chrome이 열리면 GPT Plus 로그인 확인")
            print("3. 이 워커를 다시 실행")
            print()
            print("또는 수동 실행:")
            print('  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"')
            print('  --remote-debugging-port=9222')
            print('  --user-data-dir="%LOCALAPPDATA%\\Google\\Chrome\\User Data"')
            print("="*60)
            raise ConnectionError("Chrome Debug Mode에 연결할 수 없습니다. 위 지침을 따라주세요.")


    def _human_delay(self, min_s=0.5, max_s=1.5):
        """Sleeps for a random duration to mimic human pauses."""
        time.sleep(random.uniform(min_s, max_s))

    def _human_type(self, selector: str, text: str):
        """Types text with random inter-key delays."""
        self.page.focus(selector)
        # Random initialization delay
        self._human_delay(0.5, 1.0)
        
        # Type with variance
        self.page.type(selector, text, delay=random.randint(30, 100)) 
        self._human_delay(0.5, 1.0)

    def _human_click(self, selector: str):
        """Moves mouse to element, hovers, pauses, then clicks."""
        loc = self.page.locator(selector).first
        if loc.count() > 0:
            box = loc.bounding_box()
            if box:
                # Move to random point within the element
                x = box["x"] + box["width"] * random.uniform(0.2, 0.8)
                y = box["y"] + box["height"] * random.uniform(0.2, 0.8)
                self.page.mouse.move(x, y, steps=10)
                self._human_delay(0.2, 0.5)
                self.page.mouse.click(x, y)
            else:
                loc.click()
        else:
            # Fallback
            loc.click()

    def ensure_on_page(self, url: str):
        """Navigates to URL if not current."""
        if self.page.url != url:
            print(f"[Worker] Navigating to: {url}")
            self.page.goto(url)
            self.page.wait_for_load_state("domcontentloaded")
            self._human_delay(1.0, 2.0)

    def _get_last_assistant_message(self) -> Optional[Locator]:
        """Finds the last assistant message using fallback selectors."""
        # Strategy 1: Role based (Successor of current GPT UI)
        loc = self.page.locator('div[data-message-author-role="assistant"]').last
        if loc.count() > 0:
            return loc

        # Strategy 2: TestID based
        # Usually Conversation turns have data-testid="conversation-turn-X"
        # We need to find the one that does NOT have user icon or has specific class
        # This is harder to generalize, stick to role or class.
        
        return None

    def _monitor_response_state_machine(self, current_turn_count: int) -> str:
        """
        Implements the 4-phase State Machine for Robust Response Extraction.
        
        States:
        1. WAIT_START: Waiting for indication of response (streaming cursor, stop button, or new message).
        2. STREAMING: Indicated by "Stop generating" button or "streaming" class.
        3. STABILIZING: No streaming indicators, checking if text is growing or static.
        4. DONE: Text is stable and stream ended.
        """
        
        print("[Worker] State: WAIT_START")
        
        # Max wait for start: 30s (GPT can be slow)
        start_wait_limit = 30
        start_time = time.time()
        
        # Selectors
        stop_btn_sel = 'button[aria-label="Stop generating"]'
        result_streaming_sel = '.result-streaming' # Legacy, but sometimes used
        
        state = "WAIT_START"
        last_text_len = 0
        stable_since = 0
        
        # Target loop frequency: ~300ms
        while True:
            now = time.time()
            
            # --- Check Indicators ---
            stop_btn = self.page.locator(stop_btn_sel)
            is_streaming = False
            try:
                if stop_btn.count() > 0 and stop_btn.is_visible():
                    is_streaming = True
            except:
                pass

            # Count messages
            assist_msgs = self.page.locator('div[data-message-author-role="assistant"]')
            msg_count = assist_msgs.count()
            
            # --- State Transitions ---

            if state == "WAIT_START":
                # Exit conditions
                if is_streaming:
                    state = "STREAMING"
                    print("[Worker] State: STREAMING (Stop button detected)")
                elif msg_count > current_turn_count:
                    # New message appeared but maybe processed very fast
                    state = "STREAMING" 
                    print("[Worker] State: STREAMING (New message detected)")
                
                # Timeout
                if now - start_time > start_wait_limit:
                    raise TimeoutError("Waited 30s but response did not start.")

            elif state == "STREAMING":
                # Logic: wait until streaming signals are gone
                if msg_count > current_turn_count:
                    last_msg = assist_msgs.last
                    content = last_msg.inner_text()
                    if not is_streaming and len(content) > last_text_len:
                        # It grew, so it's still "effectively" streaming even if button blinked out
                        pass
                    
                    if not is_streaming:
                        # Potential transition to STABILIZING
                        state = "STABILIZING"
                        stable_since = now
                        last_text_len = len(content)
                        print(f"[Worker] State: STABILIZING (Len: {last_text_len})")
                
                elif not is_streaming:
                     # Weird case: no new message yet but stop button is gone? 
                     # Might be network delay or glitch. Go back to WAIT_START if barely any time passed
                     if now - start_time > 5:
                         state = "STABILIZING" # Assume done?

            elif state == "STABILIZING":
                # Logic: Ensure text length is constant for X seconds
                current_msg = assist_msgs.last
                current_text = current_msg.inner_text()
                current_len = len(current_text)

                if is_streaming:
                    # Reverted to streaming?
                    state = "STREAMING"
                    print("[Worker] State: STREAMING (Resume)")
                    continue

                if current_len != last_text_len:
                    # Changed! Reset timer
                    last_text_len = current_len
                    stable_since = now
                    # print(f"   -> Growing... {current_len}")
                else:
                    # Stable?
                    stability_duration = now - stable_since
                    # Criteria: > 2.0s stable AND minimum length > 10
                    if stability_duration > 2.0 and current_len > 10:
                        print(f"[Worker] State: DONE (Stable for {stability_duration:.1f}s)")
                        return current_text

                # Safety timeout (Stabilizing too long - e.g. 2 mins)
                if now - start_time > 180:
                    print("[Worker] Warning: Timeout in stabilizing. Returning what we have.")
                    return current_text

            time.sleep(0.3)

    def send_message_and_get_response(self, text: str, gpt_url: str) -> str:
        """Core workflow for one interaction."""
        if not self.page:
            self.start_browser()

        self.ensure_on_page(gpt_url)

        # 1. Get initial state
        assist_msgs = self.page.locator('div[data-message-author-role="assistant"]')
        try:
            initial_count = assist_msgs.count()
        except:
            initial_count = 0
            
        print(f"[Worker] Initial Message Count: {initial_count}")

        # 2. Input and Send
        textbox = '#prompt-textarea'
        send_btn = 'button[data-testid="send-button"]'
        
        try:
            self.page.wait_for_selector(textbox, state="visible", timeout=10000)
        except:
            print("⚠️ Cloudflare check or login needed? Waiting longer...")
            self.page.wait_for_selector(textbox, state="visible", timeout=30000)

        # Sanity: if text is empty, don't send
        if not text.strip():
            return ""

        print(f"[Worker] Typing message... ({len(text)} chars)")
        self._human_type(textbox, text)
        
        # Wait for send button to be enabled/visible
        self.page.wait_for_selector(send_btn, state="visible", timeout=5000)
        self._human_click(send_btn)

        # 3. Monitor Response
        response_text = self._monitor_response_state_machine(initial_count)
        
        # 4. Post-processing
        # Remove potential artifacts or "Searching web..." lines if generic text is requested
        # For now, return raw innerText as requested by the user ("checking last assistant message")
        return response_text

    def run_video_generation_workflow(self, initial_story: str) -> dict:
        """
        Orchestrates the 3-step workflow.
        """
        results = {}
        try:
            print("\n=== 🚀 Starting Smart Workflow (System Profile) ===")
            
            # Step 1
            print("\n📍 Step 1: Fable Forge (Story Expansion)")
            fable_prompt = f"{initial_story}\n\n이 이야기를 기승전결이 확실한, 재밌는 이야기로 풍성하게 만들어줘"
            results["expanded_story"] = self.send_message_and_get_response(
                fable_prompt, self.GPT_URLS["fable_forge"]
            )
            print(f"✅ Step 1 Done. Length: {len(results['expanded_story'])}")
            
            self._human_delay(2, 4)

            # Step 2
            print("\n📍 Step 2: Storyboard GPT")
            sb_prompt = f"{results['expanded_story']}\n\n이 이야기를 스토리보드로 만들어봐"
            results["storyboard"] = self.send_message_and_get_response(
                sb_prompt, self.GPT_URLS["storyboard_gpt"]
            )
            print(f"✅ Step 2 Done. Length: {len(results['storyboard'])}")

            self._human_delay(2, 4)

            # Step 3
            print("\n📍 Step 3: Storyboard Maker (Prompt Gen)")
            pm_prompt = f"{results['storyboard']}\n\n이 스토리보드를 프롬프트로 만들어봐"
            results["prompts"] = self.send_message_and_get_response(
                pm_prompt, self.GPT_URLS["storyboard_maker"]
            )
            print(f"✅ Step 3 Done. Length: {len(results['prompts'])}")

            return results

        except Exception as e:
            print(f"\n❌ Workflow Failed: {e}")
            raise e

    def close(self):
        """Clean shutdown."""
        if self.context:
            try:
                # If CDP, just disconnect
                if self.browser: 
                    self.browser.close() # Actually disconnects in Playwright python sync (Connect) check docs?
                    # Docs: browser.close() for connected browser disconnects.
                else:
                    self.context.close() # Close persistent context
            except:
                pass
        
        if self.playwright:
            self.playwright.stop()

    def __enter__(self):
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
