"""
High‑level API for automating interactions with OpenAI's ChatGPT web
interface via a real browser.  The goal of this module is to provide
a clean entry point for launching a browser, logging in (once),
persisting the session, sending prompts and extracting responses.

Motivation
==========

OpenAI exposes official APIs for the GPT models, but some features of
the chat interface—such as custom system prompts, web search or
different model variants—are only available through the web UI.
While it is possible to automate this UI using tools like Puppeteer
or Playwright, the resulting scripts are often brittle and hard to
reuse.  This module encapsulates common patterns so you can focus
on your own application logic.

Important implementation notes
-----------------------------

* **Session persistence.**  After logging in for the first time,
  authentication cookies are saved to a JSON file.  On subsequent
  runs the cookies are restored so the browser remains logged in.
  Saving and restoring cookies is a standard pattern in browser
  automation.  For example, WebShare’s Puppeteer tutorial explains
  that you can call ``page.cookies()`` to extract cookies and write
  them to disk, then later read that file and pass the cookies
  back to ``page.setCookie()``【741551739242537†L389-L475】.  Without this
  persistence you would be prompted for credentials every time.

* **Using Playwright’s storage state.**  Playwright provides a
  convenience API for persisting the entire browser context, not just
  cookies.  Passing a ``storage_state`` file when creating a new
  context will restore local storage, cookies and other session data
  so that the user remains authenticated across runs.  The
  ``chatgpt‑automation‑mcp`` project, which automates ChatGPT via
  Playwright, notes that “browser sessions maintain login state
  across runs using Playwright's storage state feature”【143090759858972†L324-L329】.
  This module adopts the same pattern: if ``storage_state_path``
  exists, it is used when creating the context; otherwise, after
  logging in the state is written for reuse.

* **Cookies and security.**  Storing cookies or session tokens on
  disk means anyone with access to that file can impersonate the
  account.  When automize.dev discusses bypassing logins with
  cookies they caution that session tokens expire and should be
  updated regularly【199440872001240†L87-L133】.  Keep your
  ``storage_state_path`` in a secure location, and be prepared to
  re‑authenticate if the session expires.

Usage example::

    from chatgpt_automation import ChatGPTWebClient

    client = ChatGPTWebClient(
        email="you@example.com",
        password="your‑password",
        storage_state_path="~/.config/chatgpt_state.json",
        headless=False,
    )
    client.launch()
    client.ensure_login()
    reply = client.ask("Hello, how are you today?")
    print(reply)
    client.close()

This code will launch a Chromium browser, log in to chat.openai.com if
necessary, send your prompt and print ChatGPT’s response.
"""

import json
import os
from pathlib import Path
from typing import Optional

from playwright.sync_api import Playwright, sync_playwright, TimeoutError as PlaywrightTimeoutError


class ChatGPTWebClient:
    """Automate the ChatGPT web interface using Playwright.

    Parameters
    ----------
    email : str, optional
        The email address associated with your OpenAI account.  If
        provided along with ``password``, the client will attempt to
        perform the initial login automatically.  When omitted you
        must log in manually in the browser window.
    password : str, optional
        Your OpenAI password.  Only used if ``email`` is also
        provided.  For security reasons you may prefer to keep this
        ``None`` and log in manually.
    storage_state_path : str, optional
        File path where Playwright should persist and restore the
        authenticated session.  If the file exists it will be used
        when creating the browser context; if it does not exist, the
        state will be saved after a successful login.  The default is
        ``~/.chatgpt_storage_state.json``.
    headless : bool, optional
        Whether to launch the browser in headless mode.  For debugging
        or during the initial login you may wish to set this to
        ``False``.  The default is ``True``.
    slow_mo : int, optional
        Milliseconds to wait between actions.  Increasing this makes
        the automation easier to follow visually and sometimes helps
        with flakiness.  The default is 0 (no extra delay).

    Notes
    -----
    The ChatGPT web UI evolves frequently.  You may need to adjust
    selectors in ``_login`` and ``ask`` if OpenAI changes the HTML
    structure.  Running in headful mode and using your browser’s
    developer tools can help you find the correct selectors.
    """

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        storage_state_path: Optional[str] = None,
        headless: bool = True,
        slow_mo: int = 0,
    ) -> None:
        self.email = email
        self.password = password
        self.storage_state_path = Path(
            os.path.expanduser(storage_state_path or "~/.chatgpt_storage_state.json")
        )
        self.headless = headless
        self.slow_mo = slow_mo
        # Internal variables
        self._playwright: Optional[Playwright] = None
        self._browser = None
        self._context = None
        self._page = None

    # ---------------------------------------------------------------------
    # Lifecycle management
    # ---------------------------------------------------------------------
    def launch(self) -> None:
        """Launch the browser and create a new context/page.

        If a storage state file exists, it is passed to ``new_context`` so
        that the user remains logged in across runs.  Otherwise a fresh
        context is created.
        """
        if self._playwright is not None:
            raise RuntimeError("Browser already launched")
        self._playwright = sync_playwright().start()
        browser = self._playwright.chromium.launch(headless=self.headless, slow_mo=self.slow_mo)
        self._browser = browser
        context_kwargs = {}
        if self.storage_state_path.exists():
            context_kwargs["storage_state"] = str(self.storage_state_path)
        self._context = browser.new_context(**context_kwargs)
        self._page = self._context.new_page()

    def close(self) -> None:
        """Close the browser and Playwright engine."""
        if self._page is not None:
            try:
                self._page.close()
            except Exception:
                pass
            self._page = None
        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    # ---------------------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------------------
    def ensure_login(self, timeout: int = 300_000) -> None:
        """Ensure that we are logged into ChatGPT.

        This method navigates to chat.openai.com and attempts to detect
        whether a login is required.  If the user is already
        authenticated (e.g. from a persisted session), it returns
        immediately.  Otherwise it will call :meth:`_login` to perform
        the login procedure.

        Parameters
        ----------
        timeout : int
            Maximum time in milliseconds to wait for the login page
            elements.  Increase this if your connection is slow.
        """
        if self._page is None:
            raise RuntimeError("Browser not launched. Call launch() first.")
        page = self._page
        page.goto("https://chat.openai.com/", timeout=timeout)
        try:
            # Try to detect the message input area; if it exists we are already logged in.
            page.wait_for_selector(self._prompt_textarea_selector(), timeout=10_000)
            return  # Already logged in
        except PlaywrightTimeoutError:
            # Not logged in; attempt login if credentials are provided.
            if not self.email or not self.password:
                raise RuntimeError(
                    "No valid session and no credentials provided. "
                    "Please log in manually by launching headful and supply email/password."
                )
            self._login(timeout=timeout)

    def _login(self, timeout: int = 300_000) -> None:
        """Perform the login flow using the provided credentials.

        This function navigates to ChatGPT’s login page, fills the email
        and password fields, handles potential redirections, and waits
        until the chat input appears.  Once logged in successfully it
        writes the current browser storage state to ``storage_state_path``
        so that future runs can skip the login step.  You may need to
        adapt the selectors if OpenAI updates their login form.
        """
        page = self._page
        # Navigate to login page
        page.goto("https://chat.openai.com/auth/login", timeout=timeout)
        # Wait for the email input
        try:
            page.wait_for_selector("input[type=email]", timeout=30_000)
        except PlaywrightTimeoutError:
            raise RuntimeError("Could not find email input on login page. UI may have changed.")
        # Fill email and submit
        page.fill("input[type=email]", self.email)
        page.click("button[type=submit],button:has-text('Continue'),button:has-text('계속')")
        # Wait for password field (there may be a redirect)
        try:
            page.wait_for_selector("input[type=password]", timeout=60_000)
        except PlaywrightTimeoutError:
            raise RuntimeError("Password input not found during login. Check 2FA or UI changes.")
        page.fill("input[type=password]", self.password)
        page.click("button[type=submit],button:has-text('Continue'),button:has-text('계속')")
        # Wait until chat UI loads
        try:
            page.wait_for_selector(self._prompt_textarea_selector(), timeout=120_000)
        except PlaywrightTimeoutError:
            raise RuntimeError(
                "Login did not finish in time. It might require CAPTCHA or additional verification."
            )
        # Persist session
        self._context.storage_state(path=str(self.storage_state_path))

    # ---------------------------------------------------------------------
    # Chatting
    # ---------------------------------------------------------------------
    def ask(self, prompt: str, timeout: int = 120_000) -> str:
        """Send a prompt to ChatGPT and return the assistant's response.

        Parameters
        ----------
        prompt : str
            The user message to send.
        timeout : int
            Maximum time in milliseconds to wait for a response.  If
            ChatGPT takes longer than this to reply, a
            ``PlaywrightTimeoutError`` is raised.

        Returns
        -------
        response : str
            The assistant's message as plain text (markdown stripped).
        """
        page = self._page
        # Ensure we are on the chat page
        if not page.url.startswith("https://chat.openai.com"):
            page.goto("https://chat.openai.com/", timeout=60_000)
        # Focus textarea, type message and send
        textarea_selector = self._prompt_textarea_selector()
        try:
            textarea = page.wait_for_selector(textarea_selector, timeout=20_000)
        except PlaywrightTimeoutError:
            raise RuntimeError("Prompt textarea not found; ensure you are logged in and the UI is loaded.")
        textarea.click()
        textarea.fill(prompt)
        # ChatGPT uses Enter to submit; shift+Enter for newline
        textarea.press("Enter")
        # Wait for the assistant message to finish streaming
        response_selector = self._assistant_message_selector()
        # Wait for at least one assistant message to appear
        page.wait_for_selector(response_selector, timeout=timeout)
        # Poll until the "typing" indicator disappears; ChatGPT uses an
        # SVG spinner with aria-label="Stop generating" when streaming.
        # We wait until that button disappears to ensure the response
        # finished.
        try:
            page.wait_for_selector("button[aria-label='Stop generating']", timeout=timeout, state="detached")
        except PlaywrightTimeoutError:
            # Either timed out or the UI changed; proceed to extract anyway
            pass
        # Grab the last assistant message
        messages = page.query_selector_all(response_selector)
        if not messages:
            raise RuntimeError("No assistant messages found after sending prompt.")
        last_message = messages[-1]
        content = last_message.inner_text()
        return content.strip()

    # ---------------------------------------------------------------------
    # Selector helpers
    # ---------------------------------------------------------------------
    @staticmethod
    def _prompt_textarea_selector() -> str:
        """Return a CSS selector for the chat input textarea.

        The ChatGPT UI has used various attribute combinations for the
        prompt textarea.  We use a flexible selector that matches a
        textarea with a placeholder hint for sending messages.
        """
        # The aria-label or placeholder may vary by locale; we match either.
        return "textarea[placeholder*='Send a message'][aria-label], textarea[data-testid='prompt-textarea']"

    @staticmethod
    def _assistant_message_selector() -> str:
        """Return a CSS selector for assistant message bubbles.

        Assistant messages are wrapped in elements with a data attribute
        indicating their role.  This selector matches the inner
        markdown container so that text can be extracted easily.
        """
        return "div[data-message-author-role='assistant'] div.markdown"

    # ---------------------------------------------------------------------
    # Convenience context manager
    # ---------------------------------------------------------------------
    def __enter__(self):
        self.launch()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()