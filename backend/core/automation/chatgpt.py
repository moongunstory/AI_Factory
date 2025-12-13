import os
import time
import asyncio
from playwright.async_api import async_playwright, Page, BrowserContext

class ChatGPTClient:
    # 3개의 커스텀 GPT URL
    GPT_URLS = {
        "fable_forge": "https://chatgpt.com/g/g-mBqCBRe17-fable-forge",
        "storyboard_gpt": "https://chatgpt.com/g/g-fPCGX4kUc-storyboard-gpt",
        "storyboard_maker": "https://chatgpt.com/g/g-jtTGRSqZ9-storyboard-maker"
    }

    def __init__(self, user_data_dir: str = None):
        # 기본 경로를 프로젝트 루트의 .chrome_profile로 설정
        if user_data_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            user_data_dir = os.path.join(project_root, ".chrome_profile")
        self.user_data_dir = os.path.abspath(user_data_dir)
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

    async def ensure_on_target_page(self, gpt_url: str):
        """Navigates to the specified GPT if not already there."""
        if self.page.url != gpt_url:
            await self.page.goto(gpt_url)
            # Wait for potential redirects or loading
            await self.page.wait_for_load_state("networkidle")
            # 페이지 로드 후 약간의 대기
            await asyncio.sleep(1)

    async def send_message_and_get_response(self, text: str, gpt_url: str):
        """
        Types the text, sends it, waits for generation, and returns the response.
        """
        if not self.page:
            await self.start_browser()

        await self.ensure_on_target_page(gpt_url)

        # Check if we are logged in by looking for the textarea
        textarea_selector = "#prompt-textarea"
        login_required = False

        try:
            # 먼저 짧게 확인 (5초)
            await self.page.wait_for_selector(textarea_selector, timeout=5000)
        except:
            # textarea가 없으면 로그인이 필요할 수 있음
            login_required = True
            print("\n" + "="*60)
            print("ChatGPT 로그인이 필요합니다.")
            print("열린 브라우저 창에서 로그인을 완료해주세요.")
            print("로그인 후 자동으로 진행됩니다. (최대 5분 대기)")
            print("="*60 + "\n")

            # 사용자가 로그인할 수 있도록 충분한 시간 제공 (5분)
            try:
                await self.page.wait_for_selector(textarea_selector, timeout=300000)  # 5분
                print("\n✓ 로그인이 확인되었습니다. 작업을 계속합니다.\n")
            except:
                raise Exception(
                    "로그인 시간이 초과되었습니다. "
                    "브라우저 창에서 ChatGPT에 로그인한 후 다시 시도해주세요."
                )

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
        """
        results = {}

        try:
            # 브라우저 시작
            if not self.page:
                await self.start_browser()

            print("=== Step 1: 이야기 확장 (Fable Forge) ===")
            # Step 1: Fable Forge - 이야기 확장
            fable_prompt = f"{initial_story}\n\n이 이야기를 기승전결이 확실한, 재밌는 이야기로 풍성하게 만들어줘"
            expanded_story = await self.send_message_and_get_response(
                fable_prompt,
                self.GPT_URLS["fable_forge"]
            )
            results["expanded_story"] = expanded_story
            print(f"✓ 이야기 확장 완료 (길이: {len(expanded_story)} 문자)")

            # 다음 단계로 넘어가기 전 잠시 대기
            await asyncio.sleep(2)

            print("=== Step 2: 스토리보드 작성 (Storyboard GPT) ===")
            # Step 2: Storyboard GPT - 스토리보드 작성
            storyboard_prompt = f"{expanded_story}\n\n이 이야기를 스토리보드로 만들어봐"
            storyboard = await self.send_message_and_get_response(
                storyboard_prompt,
                self.GPT_URLS["storyboard_gpt"]
            )
            results["storyboard"] = storyboard
            print(f"✓ 스토리보드 작성 완료 (길이: {len(storyboard)} 문자)")

            # 다음 단계로 넘어가기 전 잠시 대기
            await asyncio.sleep(2)

            print("=== Step 3: 프롬프트 생성 (Storyboard Maker) ===")
            # Step 3: Storyboard Maker - 프롬프트 생성
            prompt_generation_prompt = f"{storyboard}\n\n이 스토리보드를 프롬프트로 만들어봐"
            prompts = await self.send_message_and_get_response(
                prompt_generation_prompt,
                self.GPT_URLS["storyboard_maker"]
            )
            results["prompts"] = prompts
            print(f"✓ 프롬프트 생성 완료 (길이: {len(prompts)} 문자)")

            print("=== 워크플로우 완료! ===")
            return results

        except Exception as e:
            print(f"워크플로우 에러: {e}")
            raise e
