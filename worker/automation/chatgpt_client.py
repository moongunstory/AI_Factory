"""동기 Playwright ChatGPT 클라이언트 - asyncio 충돌 없음"""
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError


class ChatGPTClient:
    """동기 Playwright 클라이언트 - Windows asyncio 충돌 해결"""

    # 3개의 커스텀 GPT URL
    GPT_URLS = {
        "fable_forge": "https://chatgpt.com/g/g-mBqCBRe17-fable-forge",
        "storyboard_gpt": "https://chatgpt.com/g/g-fPCGX4kUc-storyboard-gpt",
        "storyboard_maker": "https://chatgpt.com/g/g-jtTGRSqZ9-storyboard-maker"
    }

    def __init__(self, user_data_dir: str = None, storage_state_path: str = None):
        # 기본 경로를 프로젝트 루트의 .chrome_profile로 설정
        if user_data_dir is None:
            project_root = Path(__file__).parent.parent.parent
            user_data_dir = str(project_root / ".chrome_profile")
        self.user_data_dir = os.path.abspath(user_data_dir)

        # Storage state 경로 (세션 persistence를 위한)
        if storage_state_path is None:
            project_root = Path(__file__).parent.parent.parent
            storage_state_path = str(project_root / ".chatgpt_storage_state.json")
        self.storage_state_path = Path(storage_state_path)

        self.playwright = None
        self.browser_context: BrowserContext = None
        self.page: Page = None

    def start_browser(self):
        """브라우저 시작 (동기)"""
        if self.page and not self.page.is_closed():
            return

        print("[Worker] 브라우저 시작 중...")

        self.playwright = sync_playwright().start()

        # Prepare context options
        context_options = {
            "headless": False,  # Headed mode for debugging
            "channel": "chrome",  # Use installed Chrome
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
            "viewport": {"width": 1280, "height": 800}
        }

        # Load storage state if exists
        if self.storage_state_path.exists():
            print(f"[Worker] 저장된 세션 상태 로드: {self.storage_state_path}")
            context_options["storage_state"] = str(self.storage_state_path)

        # Launch persistent context
        self.browser_context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            **context_options
        )

        # Get the first page or create new one
        if self.browser_context.pages:
            self.page = self.browser_context.pages[0]
        else:
            self.page = self.browser_context.new_page()

        print(f"[Worker] 브라우저 준비 완료")

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
        """Return a CSS selector for the copy button."""
        return 'button[aria-label="Copy"], button[aria-label="복사"], button[aria-label="복사하기"], button[data-testid="copy-turn-action-button"]'

    def ensure_on_target_page(self, gpt_url: str):
        """Navigates to the specified GPT if not already there."""
        if self.page.url != gpt_url:
            print(f"[Worker] 페이지 이동: {gpt_url}")
            self.page.goto(gpt_url, timeout=60000)
            self.page.wait_for_load_state("networkidle")
            time.sleep(1)

    def ensure_logged_in(self):
        """로그인 확인 및 대기"""
        textarea_selector = self._prompt_textarea_selector()

        try:
            # 먼저 짧게 확인 (5초)
            self.page.wait_for_selector(textarea_selector, timeout=5000)
            print("[Worker] 이미 로그인되어 있습니다.")
            return
        except PlaywrightTimeoutError:
            # 로그인 필요
            print("\n" + "="*60)
            print("⚠️  ChatGPT 로그인이 필요합니다.")
            print("열린 브라우저 창에서 로그인을 완료해주세요.")
            print("로그인 후 자동으로 진행됩니다. (최대 5분 대기)")
            print("="*60 + "\n")

            # 5분 대기
            try:
                self.page.wait_for_selector(textarea_selector, timeout=300000)
                print("\n✅ 로그인 확인. 세션 저장 중...\n")

                # Save session state
                self.browser_context.storage_state(path=str(self.storage_state_path))
                print(f"[Worker] 세션 저장 완료: {self.storage_state_path}")

            except PlaywrightTimeoutError:
                raise Exception("로그인 시간 초과. 다시 시도해주세요.")

    def send_message_and_get_response(self, text: str, gpt_url: str) -> str:
        """메시지 전송 및 응답 수신 (동기)"""
        if not self.page:
            self.start_browser()

        self.ensure_on_target_page(gpt_url)
        self.ensure_logged_in()

        textarea_selector = self._prompt_textarea_selector()

        # Type the message
        print(f"[Worker] 메시지 전송: {text[:50]}...")
        try:
            self.page.click(textarea_selector)
            self.page.fill(textarea_selector, text)
            time.sleep(0.5)
            self.page.keyboard.press("Enter")
        except Exception as e:
            raise Exception(f"메시지 전송 실패: {str(e)}")

        # Wait for generation
        print("[Worker] 응답 대기 중...")
        time.sleep(2)

        # Wait for network idle
        try:
            self.page.wait_for_load_state("networkidle", timeout=120000)
        except PlaywrightTimeoutError:
            print("[Worker] Warning: Network idle timeout, continuing...")

        # Wait for copy button
        copy_button_selector = self._copy_button_selector()
        try:
            self.page.wait_for_selector(copy_button_selector, state="attached", timeout=120000)
            print("[Worker] 응답 생성 완료")
        except PlaywrightTimeoutError:
            print("[Worker] Warning: Copy button wait timed out, extracting anyway...")

        # Extract last response
        assistant_selector = self._assistant_message_selector()
        assistant_msgs = self.page.locator(assistant_selector)
        count = assistant_msgs.count()

        if count == 0:
            raise Exception("ChatGPT 응답을 찾을 수 없습니다.")

        last_msg = assistant_msgs.nth(count - 1)

        try:
            response_text = last_msg.inner_text()
            print(f"[Worker] 응답 수신 완료 (길이: {len(response_text)} 문자)")
            return response_text
        except Exception as e:
            raise Exception(f"응답 텍스트 추출 실패: {str(e)}")

    def close(self):
        """브라우저 종료"""
        print("[Worker] 브라우저 종료 중...")

        if self.browser_context:
            try:
                # Save session state
                if self.storage_state_path:
                    self.browser_context.storage_state(path=str(self.storage_state_path))
                    print(f"[Worker] 세션 저장: {self.storage_state_path}")
            except Exception as e:
                print(f"[Worker] Warning: Failed to save session: {e}")

            try:
                self.browser_context.close()
            except Exception as e:
                print(f"[Worker] Warning: Failed to close context: {e}")

        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as e:
                print(f"[Worker] Warning: Failed to stop playwright: {e}")

        self.browser_context = None
        self.page = None
        self.playwright = None
        print("[Worker] 브라우저 종료 완료")

    def __enter__(self):
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def run_video_generation_workflow(self, initial_story: str) -> dict:
        """
        3단계 워크플로우 실행 (동기)

        1. Fable Forge: 이야기 확장
        2. Storyboard GPT: 스토리보드 작성
        3. Storyboard Maker: 프롬프트 생성

        Returns:
            dict: {
                "expanded_story": str,
                "storyboard": str,
                "prompts": str
            }
        """
        results = {}

        try:
            if not self.page:
                self.start_browser()

            print("\n" + "="*60)
            print("=== 🎬 비디오 생성 워크플로우 시작 ===")
            print("="*60 + "\n")

            # Step 1: Fable Forge
            print("📖 Step 1/3: 이야기 확장 (Fable Forge)")
            fable_prompt = f"{initial_story}\n\n이 이야기를 기승전결이 확실한, 재밌는 이야기로 풍성하게 만들어줘"
            expanded_story = self.send_message_and_get_response(
                fable_prompt,
                self.GPT_URLS["fable_forge"]
            )
            results["expanded_story"] = expanded_story
            print(f"✅ Step 1 완료 (길이: {len(expanded_story)} 문자)\n")

            time.sleep(2)

            # Step 2: Storyboard GPT
            print("🎬 Step 2/3: 스토리보드 작성 (Storyboard GPT)")
            storyboard_prompt = f"{expanded_story}\n\n이 이야기를 스토리보드로 만들어봐"
            storyboard = self.send_message_and_get_response(
                storyboard_prompt,
                self.GPT_URLS["storyboard_gpt"]
            )
            results["storyboard"] = storyboard
            print(f"✅ Step 2 완료 (길이: {len(storyboard)} 문자)\n")

            time.sleep(2)

            # Step 3: Storyboard Maker
            print("✨ Step 3/3: 프롬프트 생성 (Storyboard Maker)")
            prompt_generation_prompt = f"{storyboard}\n\n이 스토리보드를 프롬프트로 만들어봐"
            prompts = self.send_message_and_get_response(
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
