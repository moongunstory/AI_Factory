import os
import time
import random
import subprocess
import socket
import urllib.request
from pathlib import Path
from typing import Optional, Dict

from playwright.sync_api import (
    sync_playwright,
    Page,
    BrowserContext,
    TimeoutError as PlaywrightTimeoutError,
    Locator,
)

# --- Configuration ---
AUTOMATION_PROFILE = Path(r"C:\Users\moong\AppData\Local\Google\Chrome\User Data")
CHROME_EXECUTABLE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def _pick_free_port() -> int:
    """OS가 지금 비어있는 포트를 하나 골라준다."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _wait_cdp_ready(port: int, timeout_s: int = 25) -> None:
    """
    Chrome DevTools Protocol(CDP) HTTP 엔드포인트가 실제로 열릴 때까지 기다린다.
    열리면 connect_over_cdp가 100% 안정적으로 붙는다.
    """
    url = f"http://127.0.0.1:{port}/json/version"
    end = time.time() + timeout_s
    last_err = None

    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return
        except Exception as e:
            last_err = e
            time.sleep(0.2)

    raise RuntimeError(f"CDP not ready: {url} (last={last_err})")


class ChatGPTClient:
    """
    Playwright + CDP 방식으로 '기존 크롬 프로필'을 붙잡고 자동화한다.
    핵심: Chrome을 remote-debugging-port로 띄우고, 포트가 열릴 때까지 기다린 뒤 connect_over_cdp.
    """

    GPT_URLS = {
        "fable_forge": "https://chatgpt.com/g/g-mBqCBRe17-fable-forge",
        "storyboard_gpt": "https://chatgpt.com/g/g-fPCGX4kUc-storyboard-gpt",
        "storyboard_maker": "https://chatgpt.com/g/g-jtTGRSqZ9-storyboard-maker",
    }

    def __init__(self):
        self.playwright = None
        self.browser = None  # CDP browser instance
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.user_data_dir = AUTOMATION_PROFILE
        self.browser_proc: Optional[subprocess.Popen] = None
        self.cdp_port: Optional[int] = None

    # -------------------- Browser Bootstrap --------------------

    def start_browser(self):
        """Chrome 실행 -> CDP 포트 준비 확인 -> Playwright CDP 연결."""
        if self.page and not self.page.is_closed():
            return

        profile_path = Path(self.user_data_dir)
        profile_path.mkdir(parents=True, exist_ok=True)

        # 1) Chrome 프로필 락/좀비 방지: 기존 크롬 강종
        print("[Worker] Cleaning up existing Chrome instances...")
        subprocess.run(
            "taskkill /F /IM chrome.exe",
            shell=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        time.sleep(1)

        # 2) Playwright 시작
        self.playwright = sync_playwright().start()

        # 3) 포트 자동 선택 (9222 고정 제거)
        self.cdp_port = _pick_free_port()

        cmd = [
            CHROME_EXECUTABLE,
            "--remote-debugging-address=127.0.0.1",
            f"--remote-debugging-port={self.cdp_port}",
            f"--user-data-dir={profile_path}",
            "--profile-directory=Default",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-infobars",
        ]

        print("[Worker] Launching Chrome (CDP Mode)...")
        print(f"   - User Data Dir: {profile_path}")
        print(f"   - Executable: {CHROME_EXECUTABLE}")
        print(f"   - CDP Port: {self.cdp_port}")
        print("[Chrome CMD]", " ".join(cmd))

        # 4) 크롬 실행 (stderr를 받아야 '왜 죽었는지' 알 수 있음)
        self.browser_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # 5) sleep(5) 대신: CDP 포트가 "진짜로 열릴 때까지" 기다림
        try:
            _wait_cdp_ready(self.cdp_port, timeout_s=25)
        except Exception as e:
            # 크롬이 바로 죽었으면 stderr를 뽑아 원인을 노출
            rc = self.browser_proc.poll() if self.browser_proc else None
            err_txt = ""
            if self.browser_proc and rc is not None:
                try:
                    _, err_txt = self.browser_proc.communicate(timeout=1)
                except Exception:
                    pass

            raise RuntimeError(
                "Chrome launched but CDP did not become ready.\n"
                f"- exit_code: {rc}\n"
                f"- stderr:\n{err_txt}\n"
                f"- original: {e}"
            )

        # 6) CDP로 연결
        cdp_url = f"http://127.0.0.1:{self.cdp_port}"
        print(f"[Worker] Connecting to Chrome via CDP: {cdp_url}")
        self.browser = self.playwright.chromium.connect_over_cdp(cdp_url)

        # 7) Context/Page 확보
        self.context = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()

        print("[Worker] ✅ Chrome Connected Successfully")

    # -------------------- Human-like helpers --------------------

    def _human_delay(self, min_s=0.5, max_s=1.5):
        time.sleep(random.uniform(min_s, max_s))

    def _human_click(self, selector: str):
        loc = self.page.locator(selector).first
        if loc.count() > 0:
            box = loc.bounding_box()
            if box:
                x = box["x"] + box["width"] * random.uniform(0.2, 0.8)
                y = box["y"] + box["height"] * random.uniform(0.2, 0.8)
                self.page.mouse.move(x, y, steps=10)
                self._human_delay(0.2, 0.5)
                self.page.mouse.click(x, y)
                return
        # fallback
        loc.click()

    def ensure_on_page(self, url: str):
        if self.page.url != url:
            print(f"[Worker] Navigating to: {url}")
            self.page.goto(url)
            self.page.wait_for_load_state("domcontentloaded")
            self._human_delay(1.0, 2.0)

    # -------------------- Response monitor --------------------

    def _monitor_response_state_machine(self, current_turn_count: int) -> str:
        print("[Worker] State: WAIT_START")

        start_wait_limit = 30
        start_time = time.time()
        stop_btn_sel = 'button[aria-label="Stop generating"]'

        state = "WAIT_START"
        last_text_len = 0
        stable_since = 0

        while True:
            now = time.time()

            stop_btn = self.page.locator(stop_btn_sel)
            is_streaming = False
            try:
                if stop_btn.count() > 0 and stop_btn.is_visible():
                    is_streaming = True
            except Exception:
                pass

            assist_msgs = self.page.locator('div[data-message-author-role="assistant"]')
            msg_count = assist_msgs.count()

            if state == "WAIT_START":
                if is_streaming:
                    state = "STREAMING"
                    print("[Worker] State: STREAMING (Stop button detected)")
                elif msg_count > current_turn_count:
                    state = "STREAMING"
                    print("[Worker] State: STREAMING (New message detected)")

                if now - start_time > start_wait_limit:
                    raise TimeoutError("Waited 30s but response did not start.")

            elif state == "STREAMING":
                if msg_count > current_turn_count:
                    last_msg = assist_msgs.last
                    content = last_msg.inner_text()

                    if not is_streaming:
                        state = "STABILIZING"
                        stable_since = now
                        last_text_len = len(content)
                        print(f"[Worker] State: STABILIZING (Len: {last_text_len})")

                elif not is_streaming and (now - start_time > 5):
                    state = "STABILIZING"

            elif state == "STABILIZING":
                current_msg = assist_msgs.last
                current_text = current_msg.inner_text()
                current_len = len(current_text)

                if is_streaming:
                    state = "STREAMING"
                    print("[Worker] State: STREAMING (Resume)")
                    continue

                if current_len != last_text_len:
                    last_text_len = current_len
                    stable_since = now
                else:
                    if (now - stable_since) > 2.0 and current_len > 10:
                        print(f"[Worker] State: DONE (Stable for {(now - stable_since):.1f}s)")
                        return current_text

                if now - start_time > 180:
                    print("[Worker] Warning: Timeout in stabilizing. Returning what we have.")
                    return current_text

            time.sleep(0.3)

    # -------------------- Public API --------------------

    def send_message_and_get_response(self, text: str, gpt_url: str) -> str:
        if not self.page:
            self.start_browser()

        self.ensure_on_page(gpt_url)

        assist_msgs = self.page.locator('div[data-message-author-role="assistant"]')
        try:
            initial_count = assist_msgs.count()
        except Exception:
            initial_count = 0

        print(f"[Worker] Initial Message Count: {initial_count}")

        textbox = "#prompt-textarea"
        send_btn = 'button[data-testid="send-button"]'

        try:
            self.page.wait_for_selector(textbox, state="visible", timeout=10000)
        except Exception:
            print("⚠️ Cloudflare check or login needed? Waiting longer...")
            self.page.wait_for_selector(textbox, state="visible", timeout=30000)

        if not text.strip():
            return ""

        self.page.fill(textbox, text)
        self.page.dispatch_event(textbox, "input")
        self._human_delay(0.5, 1.0)

        print("[Worker] Attempting submission via 'Enter'...")
        self.page.keyboard.press("Enter")
        self._human_delay(1.0, 2.0)

        full_text_after = self.page.input_value(textbox)
        if len(full_text_after.strip()) > 0:
            print("[Worker] 'Enter' did not send. Fallback: click Send.")
            try:
                self.page.wait_for_selector(send_btn, state="visible", timeout=3000)
                self._human_click(send_btn)
            except Exception as e:
                print(f"[Worker] Warning: Send button click failed: {e}")
        else:
            print("[Worker] Message submitted via 'Enter' successfully.")

        return self._monitor_response_state_machine(initial_count)

    def close(self):
        """Clean shutdown + 우리가 띄운 크롬 프로세스 정리."""
        try:
            if self.browser:
                # CDP 연결 해제
                self.browser.close()
        except Exception:
            pass

        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass

        # 크롬 프로세스가 살아있으면 종료
        try:
            if self.browser_proc and (self.browser_proc.poll() is None):
                self.browser_proc.terminate()
                time.sleep(0.5)
                if self.browser_proc.poll() is None:
                    self.browser_proc.kill()
        except Exception:
            pass

    def __enter__(self):
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
