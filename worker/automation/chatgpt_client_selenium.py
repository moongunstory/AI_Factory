"""Selenium + undetected-chromedriver 기반 안정적 ChatGPT 클라이언트"""
import os
import time
import platform
from pathlib import Path
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc


# --- Configuration ---
# 사용자 홈 디렉토리의 Chrome 프로필 자동 감지
def get_system_chrome_profile():
    """시스템별 기본 Chrome 프로필 경로 자동 감지"""
    system = platform.system()
    if system == "Windows":
        return Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    elif system == "Linux":
        return Path.home() / ".config" / "google-chrome"
    else:
        raise RuntimeError(f"지원하지 않는 OS: {system}")


CHROME_USER_DATA_DIR = get_system_chrome_profile()
CHROME_PROFILE_NAME = "Default"  # 또는 "Profile 1" 등
AUTOMATION_PROFILE = Path.home() / ".ai_factory_chrome_selenium"


class ChatGPTClientSelenium:
    """
    Selenium + undetected-chromedriver 기반 안정적 ChatGPT 자동화 클라이언트

    특징:
    - 봇 감지 우회 (undetected-chromedriver)
    - 기존 Chrome 프로필 사용 (로그인 세션 재사용)
    - 다중 완료 감지 (텍스트 안정성, UI 상태)
    - JavaScript fallback으로 안정성 향상
    """

    GPT_URLS = {
        "fable_forge": "https://chatgpt.com/g/g-mBqCBRe17-fable-forge",
        "storyboard_gpt": "https://chatgpt.com/g/g-fPCGX4kUc-storyboard-gpt",
        "storyboard_maker": "https://chatgpt.com/g/g-jtTGRSqZ9-storyboard-maker"
    }

    def __init__(self, use_system_profile: bool = True):
        """
        Args:
            use_system_profile: True면 시스템 Chrome 프로필 사용, False면 독립 프로필 사용
        """
        self.driver: Optional[webdriver.Chrome] = None
        self.use_system_profile = use_system_profile

        if use_system_profile:
            self.user_data_dir = CHROME_USER_DATA_DIR
            self.profile_name = CHROME_PROFILE_NAME
        else:
            self.user_data_dir = AUTOMATION_PROFILE
            self.profile_name = "Default"

    def start_browser(self):
        """브라우저 시작 (undetected-chromedriver)"""
        if self.driver:
            return

        print(f"[ChatGPT Client] Chrome 시작 중...")
        print(f"   - Profile Dir: {self.user_data_dir}")
        print(f"   - Profile Name: {self.profile_name}")

        # undetected-chromedriver 옵션 설정
        options = uc.ChromeOptions()

        # 기존 프로필 사용
        if self.use_system_profile:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
            options.add_argument(f"--profile-directory={self.profile_name}")
        else:
            # 독립 자동화 프로필
            self.user_data_dir.mkdir(parents=True, exist_ok=True)
            options.add_argument(f"--user-data-dir={self.user_data_dir}")

        # 안정성 및 감지 우회 옵션
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--start-maximized")

        # 로깅 최소화
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)

        try:
            # undetected-chromedriver로 브라우저 시작
            self.driver = uc.Chrome(options=options, use_subprocess=True)
            self.driver.implicitly_wait(10)  # 기본 대기 시간

            print("[ChatGPT Client] ✅ Chrome 시작 성공")

            # 첫 실행인지 확인
            if not self.use_system_profile:
                is_first_run = len(list(Path(self.user_data_dir).glob("*"))) < 10
                if is_first_run:
                    print("\n" + "="*60)
                    print("📋 첫 실행 - ChatGPT 로그인 필요")
                    print("="*60)
                    print("브라우저가 열리면 ChatGPT에 로그인해주세요.")
                    print("로그인 세션은 프로필에 저장되어 재사용됩니다.")
                    print("="*60 + "\n")

        except Exception as e:
            print(f"\n❌ Chrome 시작 실패: {e}")
            raise

    def _wait_for_element(self, selector: str, by=By.CSS_SELECTOR, timeout=10):
        """요소가 나타날 때까지 대기"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            print(f"⚠️ 요소를 찾을 수 없음: {selector}")
            return None

    def _wait_for_clickable(self, selector: str, by=By.CSS_SELECTOR, timeout=10):
        """요소가 클릭 가능할 때까지 대기"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            return element
        except TimeoutException:
            print(f"⚠️ 클릭 가능한 요소를 찾을 수 없음: {selector}")
            return None

    def _click_element(self, element):
        """요소 클릭 (JavaScript fallback 포함)"""
        try:
            element.click()
        except Exception:
            # JavaScript fallback
            self.driver.execute_script("arguments[0].click();", element)

    def _inject_text(self, element, text: str):
        """텍스트 직접 주입 (타이핑 우회)"""
        self.driver.execute_script("arguments[0].value = arguments[1];", element, text)

    def ensure_on_page(self, url: str):
        """특정 URL로 이동 (이미 해당 페이지면 스킵)"""
        if self.driver.current_url != url:
            print(f"[ChatGPT Client] 페이지 이동: {url}")
            self.driver.get(url)
            time.sleep(2)  # 페이지 로드 대기

    def _check_response_completed(self, initial_count: int, max_wait: int = 180) -> bool:
        """
        응답 완료 여부를 다중 방법으로 감지

        전략:
        1. Stop generating 버튼이 사라졌는지 확인
        2. 새 메시지가 추가되었는지 확인
        3. 텍스트 길이가 안정화되었는지 확인 (3초간 변화 없음)

        Returns:
            True if completed, False if timeout
        """
        start_time = time.time()
        last_text_length = 0
        stable_count = 0
        stable_threshold = 3  # 3회 연속 안정 확인

        print("[ChatGPT Client] 응답 대기 중...")

        while time.time() - start_time < max_wait:
            try:
                # 1. Stop generating 버튼 확인
                stop_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button[aria-label*="Stop"]')
                is_generating = len(stop_buttons) > 0 and any(btn.is_displayed() for btn in stop_buttons)

                # 2. Assistant 메시지 개수 확인
                assistant_messages = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    'div[data-message-author-role="assistant"]'
                )
                current_count = len(assistant_messages)

                # 새 메시지가 생성되었는지 확인
                if current_count > initial_count:
                    # 마지막 메시지의 텍스트 길이 확인
                    last_message = assistant_messages[-1]
                    current_text = last_message.text
                    current_length = len(current_text)

                    # Stop 버튼이 없고 텍스트 길이가 안정적이면 완료
                    if not is_generating:
                        if current_length == last_text_length and current_length > 0:
                            stable_count += 1
                            if stable_count >= stable_threshold:
                                print(f"[ChatGPT Client] ✅ 응답 완료 (길이: {current_length})")
                                return True
                        else:
                            stable_count = 0
                            last_text_length = current_length

                time.sleep(1)  # 1초마다 체크

            except Exception as e:
                print(f"⚠️ 응답 확인 중 오류: {e}")
                time.sleep(1)

        print(f"⚠️ 응답 대기 시간 초과 ({max_wait}초)")
        return False

    def _get_last_response(self) -> str:
        """마지막 assistant 응답 추출"""
        try:
            assistant_messages = self.driver.find_elements(
                By.CSS_SELECTOR,
                'div[data-message-author-role="assistant"]'
            )

            if assistant_messages:
                last_message = assistant_messages[-1]
                return last_message.text
            else:
                print("⚠️ Assistant 메시지를 찾을 수 없음")
                return ""

        except Exception as e:
            print(f"❌ 응답 추출 실패: {e}")
            return ""

    def send_message_and_get_response(self, text: str, gpt_url: str) -> str:
        """
        메시지 전송 및 응답 추출 (핵심 메서드)

        Args:
            text: 전송할 메시지
            gpt_url: 커스텀 GPT URL

        Returns:
            응답 텍스트
        """
        if not self.driver:
            self.start_browser()

        # 1. 해당 GPT 페이지로 이동
        self.ensure_on_page(gpt_url)

        # 2. 초기 메시지 개수 확인
        try:
            initial_messages = self.driver.find_elements(
                By.CSS_SELECTOR,
                'div[data-message-author-role="assistant"]'
            )
            initial_count = len(initial_messages)
            print(f"[ChatGPT Client] 초기 메시지 개수: {initial_count}")
        except:
            initial_count = 0

        # 3. 입력창 찾기 및 텍스트 입력
        print(f"[ChatGPT Client] 메시지 입력 중... ({len(text)} 글자)")

        textarea = self._wait_for_element("textarea#prompt-textarea", timeout=30)
        if not textarea:
            raise RuntimeError("입력창을 찾을 수 없습니다. 로그인이 필요할 수 있습니다.")

        # 텍스트 주입 (DOM 직접 조작)
        self._inject_text(textarea, text)

        # 입력 이벤트 트리거 (UI 반영)
        self.driver.execute_script("""
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, textarea)

        time.sleep(0.5)

        # 4. 전송 버튼 클릭
        send_button = self._wait_for_clickable('button[data-testid="send-button"]', timeout=10)
        if send_button:
            self._click_element(send_button)
            print("[ChatGPT Client] 메시지 전송 완료")
        else:
            # Fallback: Enter 키 입력
            textarea.send_keys(Keys.RETURN)
            print("[ChatGPT Client] Enter로 메시지 전송")

        # 5. 응답 완료 대기
        completed = self._check_response_completed(initial_count)

        if not completed:
            print("⚠️ 응답이 완료되지 않았지만 현재까지의 응답을 반환합니다.")

        # 6. 응답 추출
        response = self._get_last_response()

        return response

    def send_revision_request(self, revision_text: str, gpt_url: str, format_enforcement: str = "") -> str:
        """
        재시도(Revision) 요청

        Args:
            revision_text: 수정 요청 내용
            gpt_url: 커스텀 GPT URL
            format_enforcement: 포맷 강제 문구 (예: "답변은 JSON 형식으로만 작성")

        Returns:
            수정된 응답
        """
        full_request = f"{revision_text}\n\n{format_enforcement}" if format_enforcement else revision_text
        return self.send_message_and_get_response(full_request, gpt_url)

    def close(self):
        """브라우저 종료"""
        if self.driver:
            try:
                self.driver.quit()
                print("[ChatGPT Client] 브라우저 종료")
            except Exception as e:
                print(f"⚠️ 브라우저 종료 중 오류: {e}")
            finally:
                self.driver = None

    def __enter__(self):
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# --- 사용 예제 ---
if __name__ == "__main__":
    # 시스템 Chrome 프로필 사용 (로그인된 상태)
    client = ChatGPTClientSelenium(use_system_profile=True)

    try:
        client.start_browser()

        # 테스트 메시지
        test_prompt = "안녕하세요! 간단한 테스트 메시지입니다."

        print("\n" + "="*60)
        print("테스트: Fable Forge")
        print("="*60)

        response = client.send_message_and_get_response(
            test_prompt,
            client.GPT_URLS["fable_forge"]
        )

        print("\n[응답]")
        print(response[:500])  # 처음 500자만 출력

    finally:
        client.close()
