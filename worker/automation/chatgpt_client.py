"""Robust ChatGPT Client - Smart Automation & System Profile Support"""
import os
import time
import random
import sys
from pathlib import Path
from typing import Optional, Dict

from playwright.sync_api import sync_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError, Locator

# --- Configuration ---
# Use dedicated automation profile to avoid conflicts with running Chrome instances
AUTOMATION_PROFILE = Path.home() / ".ai_factory_chrome_profile"
CHROME_EXECUTABLE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_URL = "http://127.0.0.1:9222"  # IPv4 명시 (localhost는 IPv6로 해석될 수 있음)

class ChatGPTClient:
    """
    Robust, human-like automation for ChatGPT using a dedicated automation profile.
    Implements a State Machine for response detection and avoids API-like behavior.

    Uses a separate Chrome profile to avoid conflicts with running Chrome instances.
    First run will require ChatGPT login.
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
        self.user_data_dir = AUTOMATION_PROFILE

    def start_browser(self):
        """Starts the browser using a dedicated automation profile."""
        if self.page and not self.page.is_closed():
            return

        # Ensure automation profile directory exists
        profile_path = Path(self.user_data_dir)
        profile_path.mkdir(parents=True, exist_ok=True)

        self.playwright = sync_playwright().start()

        # Check if this is first run (profile is empty or minimal files)
        is_first_run = len(list(profile_path.glob("*"))) < 5

        print(f"[Worker] Launching Chrome (Dedicated Automation Profile)...")
        print(f"   - Profile: {profile_path}")
        print(f"   - Executable: {CHROME_EXECUTABLE}")

        if is_first_run:
            print("\n" + "="*60)
            print("📋 첫 실행 - ChatGPT 로그인 필요")
            print("="*60)
            print("브라우저가 열리면 ChatGPT에 로그인해주세요.")
            print("로그인 세션은 이 프로필에 저장되어 재사용됩니다.")
            print("="*60 + "\n")

        try:
            # Use dedicated automation profile (independent from system Chrome)
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_path),  # Convert Path to string
                executable_path=CHROME_EXECUTABLE,
                headless=False,
                args=[
                    "--no-sandbox",
                    "--disable-infobars",
                    "--disable-blink-features=AutomationControlled",  # Hide automation detection
                ],
                no_viewport=True,  # Better for user interaction
                ignore_default_args=["--enable-automation"],  # Remove automation flag
            )

            # Get the initial page
            if self.context.pages:
                self.page = self.context.pages[0]
            else:
                self.page = self.context.new_page()

            print("[Worker] ✅ Chrome Launched Successfully")

            if is_first_run:
                print("\n💡 첫 실행이므로 ChatGPT 로그인을 완료해주세요.")
                print("   로그인 후 워커를 계속 사용할 수 있습니다.\n")

        except Exception as e:
            print(f"\n❌ Chrome Launch Failed: {e}")

            # More helpful error messages
            error_str = str(e)
            if "Target closed" in error_str or "browser has been closed" in error_str:
                print("\n" + "="*60)
                print("⚠️  Chrome 시작 실패")
                print("="*60)
                print("가능한 원인:")
                print("1. Chrome이 다른 프로세스에 의해 종료됨")
                print("2. Chrome 설치 경로 확인 필요")
                print(f"   현재: {CHROME_EXECUTABLE}")
                print("3. 프로필 디렉토리 권한 문제")
                print(f"   현재: {profile_path}")
                print("\n해결 방법:")
                print("- Chrome 경로가 올바른지 확인")
                print("- 프로필 디렉토리에 쓰기 권한이 있는지 확인")
                print("- 바이러스 백신/보안 소프트웨어가 차단하는지 확인")
                print("="*60 + "\n")

            raise e


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
        Orchestrates the 3-step workflow with detailed prompting.
        """
        results = {}
        try:
            print("\n=== 🚀 Starting Smart Workflow (System Profile) ===")
            
            # Step 1: Story Expansion
            print("\n📍 Step 1: Fable Forge (Story Expansion)")
            fable_prompt = f"""다음 간단한 스토리를 기승전결이 명확한 완성도 높은 단편 이야기로 확장해주세요.

{initial_story}

요구사항:
- 사담, 부연설명, 메타 코멘트 일체 제외
- 오직 순수한 스토리 텍스트만 작성
- 명확한 기승전결 구조 (도입 → 전개 → 클라이맥스 → 결말)
- 생동감 있는 묘사와 감정선
- 캐릭터의 동기와 갈등이 명확히 드러날 것
- 독자를 몰입시킬 수 있는 디테일과 긴장감"""

            results["expanded_story"] = self.send_message_and_get_response(
                fable_prompt, self.GPT_URLS["fable_forge"]
            )
            print(f"✅ Step 1 Done. Length: {len(results['expanded_story'])}")
            
            self._human_delay(3, 5)

            # Step 2: Storyboard Generation
            print("\n📍 Step 2: Storyboard GPT")
            sb_prompt = f"""다음 스토리를 영상 제작을 위한 상세 스토리보드로 변환해주세요.

{results['expanded_story']}

요구사항:
- 사담, 설명, 메타 코멘트 일체 제외
- 각 씬(Scene)을 명확히 구분
- 씬마다 다음 요소 포함:
  * 씬 번호
  * 시간대/장소
  * 등장인물과 동작
  * 카메라 앵글/구도 제안
  * 핵심 감정/분위기
- 영상으로 시각화 가능한 구체적 묘사
- 씬 간 자연스러운 전환과 연결성
- 전체 러닝타임 1-3분 분량으로 최적화"""

            results["storyboard"] = self.send_message_and_get_response(
                sb_prompt, self.GPT_URLS["storyboard_gpt"]
            )
            print(f"✅ Step 2 Done. Length: {len(results['storyboard'])}")

            self._human_delay(3, 5)

            # Step 3: Video Prompts Generation
            print("\n📍 Step 3: Storyboard Maker (Prompt Gen)")
            pm_prompt = f"""다음 스토리보드를 바탕으로 AI 이미지 생성을 위한 최적화된 프롬프트를 제작해주세요.

{results['storyboard']}

요구사항:
- 사담, 설명, 메타 코멘트 일체 제외
- 각 씬별로 독립적인 프롬프트 생성
- 프롬프트 구성 요소:
  * 주요 피사체와 동작 (명확하고 구체적으로)
  * 배경과 환경 묘사
  * 조명과 분위기 (lighting, mood)
  * 카메라 앵글과 구도
  * 아트 스타일/화풍 지정
  * 화질 관련 키워드 (high quality, detailed, cinematic 등)
- Stable Diffusion/Midjourney 최적화 형식
- 부정 프롬프트(Negative prompt) 별도 제공
- 영문 프롬프트로 작성
- 일관된 캐릭터/스타일 유지를 위한 키워드 포함"""

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
