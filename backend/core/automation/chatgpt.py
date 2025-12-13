import os
import time
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError

class ChatGPTClient:
    # 3개의 커스텀 GPT URL
    GPT_URLS = {
        "fable_forge": "https://chatgpt.com/g/g-mBqCBRe17-fable-forge",
        "storyboard_gpt": "https://chatgpt.com/g/g-fPCGX4kUc-storyboard-gpt",
        "storyboard_maker": "https://chatgpt.com/g/g-jtTGRSqZ9-storyboard-maker"
    }

    def __init__(self, user_data_dir: str = None, storage_state_path: str = None):
        # 기본 경로를 프로젝트 루트의 .chrome_profile로 설정
        if user_data_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            user_data_dir = os.path.join(project_root, ".chrome_profile")
        self.user_data_dir = os.path.abspath(user_data_dir)

        # Storage state 경로 (세션 persistence를 위한)
        if storage_state_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            storage_state_path = os.path.join(project_root, ".chatgpt_storage_state.json")
        self.storage_state_path = Path(storage_state_path)

        self.browser_context: BrowserContext = None
        self.page: Page = None
        self.playwright = None

    async def start_browser(self):
        """
        Starts the browser with a persistent context.
        This allows cookies/login state to be saved and restored across sessions.
        """
        if self.page and not self.page.is_closed():
            return

        self.playwright = await async_playwright().start()

        # Prepare context options
        context_options = {
            "headless": False,  # Headed mode so user can see/login
            "channel": "chrome", # Use installed Chrome if available for better realism
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
            "viewport": {"width": 1280, "height": 800}
        }

        # Load storage state if exists (for session persistence)
        if self.storage_state_path.exists():
            print(f"[ChatGPTClient] 저장된 세션 상태 로드 중: {self.storage_state_path}")
            context_options["storage_state"] = str(self.storage_state_path)

        # Launch options for stability and stealth
        self.browser_context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            **context_options
        )

        # Get the first page or create new one
        if self.browser_context.pages:
            self.page = self.browser_context.pages[0]
        else:
            self.page = await self.browser_context.new_page()

        print(f"[ChatGPTClient] 브라우저 시작됨 (user_data_dir: {self.user_data_dir})")

    # ---------------------------------------------------------------------
    # Selector helpers (for easy UI changes adaptation)
    # ---------------------------------------------------------------------
    @staticmethod
    def _prompt_textarea_selector() -> str:
        """Return a CSS selector for the chat input textarea."""
        return "#prompt-textarea"

    @staticmethod
    def _assistant_message_selector() -> str:
        """Return a CSS selector for assistant message bubbles."""
        return 'div[data-message-author-role="assistant"]'

    @staticmethod
    def _copy_button_selector() -> str:
        """Return a CSS selector for the copy button (appears when response is done)."""
        return 'button[aria-label="Copy"]'

    # ---------------------------------------------------------------------
    # Navigation & Login helpers
    # ---------------------------------------------------------------------
    async def ensure_on_target_page(self, gpt_url: str):
        """Navigates to the specified GPT if not already there."""
        if self.page.url != gpt_url:
            print(f"[ChatGPTClient] 페이지 이동 중: {gpt_url}")
            await self.page.goto(gpt_url, timeout=60000)
            # Wait for potential redirects or loading
            await self.page.wait_for_load_state("networkidle")
            # 페이지 로드 후 약간의 대기
            await asyncio.sleep(1)

    async def ensure_logged_in(self):
        """
        Ensure the user is logged in to ChatGPT.
        Waits for login if necessary and saves the session state.
        """
        textarea_selector = self._prompt_textarea_selector()

        try:
            # 먼저 짧게 확인 (5초)
            await self.page.wait_for_selector(textarea_selector, timeout=5000)
            print("[ChatGPTClient] 이미 로그인되어 있습니다.")
            return  # Already logged in
        except PlaywrightTimeoutError:
            # textarea가 없으면 로그인이 필요
            print("\n" + "="*60)
            print("⚠️  ChatGPT 로그인이 필요합니다.")
            print("열린 브라우저 창에서 로그인을 완료해주세요.")
            print("로그인 후 자동으로 진행됩니다. (최대 5분 대기)")
            print("="*60 + "\n")

            # 사용자가 로그인할 수 있도록 충분한 시간 제공 (5분)
            try:
                await self.page.wait_for_selector(textarea_selector, timeout=300000)  # 5분
                print("\n✅ 로그인이 확인되었습니다. 세션 상태를 저장합니다.\n")

                # Save session state after successful login
                await self.browser_context.storage_state(path=str(self.storage_state_path))
                print(f"[ChatGPTClient] 세션 상태 저장 완료: {self.storage_state_path}")

            except PlaywrightTimeoutError:
                raise Exception(
                    "로그인 시간이 초과되었습니다. "
                    "브라우저 창에서 ChatGPT에 로그인한 후 다시 시도해주세요."
                )

    # ---------------------------------------------------------------------
    # Chatting
    # ---------------------------------------------------------------------
    async def send_message_and_get_response(self, text: str, gpt_url: str):
        """
        Types the text, sends it, waits for generation, and returns the response.
        """
        if not self.page:
            await self.start_browser()

        await self.ensure_on_target_page(gpt_url)

        # Ensure we are logged in
        await self.ensure_logged_in()

        textarea_selector = self._prompt_textarea_selector()

        # Type the message
        print(f"[ChatGPTClient] 메시지 전송 중: {text[:50]}...")
        try:
            await self.page.click(textarea_selector)
            await self.page.fill(textarea_selector, text)

            # Give a small pause
            await asyncio.sleep(0.5)

            # Send (Enter key is usually safest)
            await self.page.keyboard.press("Enter")
        except Exception as e:
            raise Exception(f"메시지 전송 실패: {str(e)}")

        # === WAIT FOR GENERATION ===
        print("[ChatGPTClient] 응답 대기 중...")

        # Wait a bit for the request to process
        await asyncio.sleep(2)

        # Wait for network idle as a heuristic
        try:
            await self.page.wait_for_load_state("networkidle", timeout=120000)
        except PlaywrightTimeoutError:
            print("[ChatGPTClient] Warning: Network idle timeout, continuing...")

        # Wait for the 'Copy' button to appear (indicates response is complete)
        copy_button_selector = self._copy_button_selector()
        try:
            await self.page.wait_for_selector(copy_button_selector, state="attached", timeout=120000)
            print("[ChatGPTClient] 응답 생성 완료 감지")
        except PlaywrightTimeoutError:
            print("[ChatGPTClient] Warning: Copy button wait timed out, attempting to extract response anyway...")

        # === EXTRACT LAST RESPONSE ===
        assistant_selector = self._assistant_message_selector()
        assistant_msgs = self.page.locator(assistant_selector)
        count = await assistant_msgs.count()

        if count == 0:
            raise Exception(
                "ChatGPT 응답을 찾을 수 없습니다. "
                "페이지가 올바르게 로드되지 않았거나 UI가 변경되었을 수 있습니다."
            )

        last_msg = assistant_msgs.nth(count - 1)

        # Get the text content
        try:
            response_text = await last_msg.inner_text()
            print(f"[ChatGPTClient] 응답 수신 완료 (길이: {len(response_text)} 문자)")
            return response_text
        except Exception as e:
            raise Exception(f"응답 텍스트 추출 실패: {str(e)}")

    async def close(self):
        """Close the browser and cleanup resources."""
        print("[ChatGPTClient] 브라우저 종료 중...")
        if self.browser_context:
            try:
                # Save session state before closing
                if self.storage_state_path:
                    await self.browser_context.storage_state(path=str(self.storage_state_path))
                    print(f"[ChatGPTClient] 세션 상태 최종 저장: {self.storage_state_path}")
            except Exception as e:
                print(f"[ChatGPTClient] Warning: Failed to save session state: {e}")

            try:
                await self.browser_context.close()
            except Exception as e:
                print(f"[ChatGPTClient] Warning: Failed to close browser context: {e}")

        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as e:
                print(f"[ChatGPTClient] Warning: Failed to stop playwright: {e}")

        self.browser_context = None
        self.page = None
        self.playwright = None
        print("[ChatGPTClient] 브라우저 종료 완료")

    # ---------------------------------------------------------------------
    # Context manager support
    # ---------------------------------------------------------------------
    async def __aenter__(self):
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    # ---------------------------------------------------------------------
    # Video Generation Workflow
    # ---------------------------------------------------------------------
    async def run_video_generation_workflow(self, initial_story: str):
        """
        3단계 워크플로우를 실행합니다:
        1. Fable Forge: 이야기 확장
        2. Storyboard GPT: 스토리보드 작성
        3. Storyboard Maker: 프롬프트 생성

        Returns:
            dict: {
                "expanded_story": str,
                "storyboard": str,
                "prompts": str
            }

        Raises:
            Exception: 워크플로우 실행 중 오류 발생 시
        """
        results = {}

        try:
            # 브라우저 시작
            if not self.page:
                await self.start_browser()

            print("\n" + "="*60)
            print("=== 🎬 비디오 생성 워크플로우 시작 ===")
            print("="*60 + "\n")

            # Step 1: Fable Forge - 이야기 확장
            print("📖 Step 1/3: 이야기 확장 (Fable Forge)")
            fable_prompt = f"{initial_story}\n\n이 이야기를 기승전결이 확실한, 재밌는 이야기로 풍성하게 만들어줘"
            expanded_story = await self.send_message_and_get_response(
                fable_prompt,
                self.GPT_URLS["fable_forge"]
            )
            results["expanded_story"] = expanded_story
            print(f"✅ Step 1 완료 (길이: {len(expanded_story)} 문자)\n")

            # 다음 단계로 넘어가기 전 잠시 대기
            await asyncio.sleep(2)

            # Step 2: Storyboard GPT - 스토리보드 작성
            print("🎬 Step 2/3: 스토리보드 작성 (Storyboard GPT)")
            storyboard_prompt = f"{expanded_story}\n\n이 이야기를 스토리보드로 만들어봐"
            storyboard = await self.send_message_and_get_response(
                storyboard_prompt,
                self.GPT_URLS["storyboard_gpt"]
            )
            results["storyboard"] = storyboard
            print(f"✅ Step 2 완료 (길이: {len(storyboard)} 문자)\n")

            # 다음 단계로 넘어가기 전 잠시 대기
            await asyncio.sleep(2)

            # Step 3: Storyboard Maker - 프롬프트 생성
            print("✨ Step 3/3: 프롬프트 생성 (Storyboard Maker)")
            prompt_generation_prompt = f"{storyboard}\n\n이 스토리보드를 프롬프트로 만들어봐"
            prompts = await self.send_message_and_get_response(
                prompt_generation_prompt,
                self.GPT_URLS["storyboard_maker"]
            )
            results["prompts"] = prompts
            print(f"✅ Step 3 완료 (길이: {len(prompts)} 문자)\n")

            print("="*60)
            print("=== 🎉 워크플로우 완료! ===")
            print("="*60 + "\n")

            return results

        except Exception as e:
            print(f"\n❌ 워크플로우 에러: {e}")
            print("="*60 + "\n")
            raise e
