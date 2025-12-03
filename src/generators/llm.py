"""LLM generator using llama-server HTTP API.

이 모듈은 llama.cpp의 llama-server와 HTTP로 통신합니다.
기존의 subprocess 기반 llama-cli 실행 방식을 대체하여 성능을 대폭 향상시킵니다.

주요 개선사항:
- 모델을 매번 로드하지 않음 (10-50배 속도 향상)
- persistent HTTP 연결 사용
- 메모리 사용량 대폭 감소
- 동시 요청 처리 가능
"""
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..common.config import Config
from ..common.logger import setup_logger
from ..common.json_utils import safe_parse

logger = setup_logger(__name__)


class LlamaClient:
    """Client for interacting with llama-server via HTTP API.

    이 클라이언트는 llama-server가 이미 실행 중이라고 가정합니다.
    llama-server는 llama_server_manager.ps1로 관리됩니다.
    """

    def __init__(
        self,
        server_url: Optional[str] = None,
        temperature: float = Config.LLM_TEMPERATURE,
        max_tokens: int = Config.LLM_MAX_TOKENS,
        top_p: float = Config.LLM_TOP_P,
        timeout: int = Config.LLM_REQUEST_TIMEOUT,
    ):
        """Initialize the Llama client.

        Args:
            server_url: llama-server URL (기본값: Config.LLAMA_SERVER_URL)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            timeout: Request timeout in seconds
        """
        self.server_url = server_url or Config.LLAMA_SERVER_URL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.timeout = timeout

        # HTTP 세션 설정 (연결 재사용)
        self.session = requests.Session()

        # Retry 전략: 연결 실패 시 3번까지 재시도
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.info(f"Initialized LlamaClient with server: {self.server_url}")

        # 서버 연결 확인
        self._check_server_health()

    def _check_server_health(self) -> None:
        """Check if llama-server is running and healthy."""
        try:
            response = self.session.get(
                f"{self.server_url}/health",
                timeout=Config.LLM_CONNECT_TIMEOUT
            )
            if response.status_code == 200:
                logger.info("✓ llama-server is healthy and ready")
            else:
                logger.warning(f"llama-server returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            error_msg = (
                f"Failed to connect to llama-server at {self.server_url}\n"
                f"Error: {e}\n\n"
                f"llama-server가 실행 중인지 확인하세요:\n"
                f"  powershell -ExecutionPolicy Bypass -File llama_server_manager.ps1 -Action status\n"
                f"실행되지 않았다면:\n"
                f"  powershell -ExecutionPolicy Bypass -File llama_server_manager.ps1 -Action start"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> str:
        """Generate text using llama-server API.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            stream: Enable streaming (기본값: False)

        Returns:
            Generated text

        Raises:
            RuntimeError: If generation fails
        """
        # Build the full prompt with system prompt if provided
        if system_prompt:
            # Format expected by Solar-10.7B-Instruct
            full_prompt = f"### System:\n{system_prompt}\n\n### User:\n{prompt}\n\n### Assistant:\n"
        else:
            full_prompt = prompt

        # Build request payload
        payload = {
            "prompt": full_prompt,
            "n_predict": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "top_p": self.top_p,
            "stream": stream,
            "cache_prompt": True,  # 프롬프트 캐싱 활성화 (속도 향상)
            "stop": ["### User:", "### System:"],  # Stop sequences
        }

        logger.info(f"Generating text (prompt length: {len(full_prompt)} chars)")
        logger.debug(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        start_time = time.time()

        try:
            response = self.session.post(
                f"{self.server_url}/completion",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            result = response.json()
            generated_text = result.get("content", "").strip()

            elapsed = time.time() - start_time
            tokens_generated = result.get("tokens_predicted", 0)
            tokens_per_sec = tokens_generated / elapsed if elapsed > 0 else 0

            logger.info(
                f"Generated {len(generated_text)} characters "
                f"({tokens_generated} tokens) in {elapsed:.2f}s "
                f"({tokens_per_sec:.1f} tokens/sec)"
            )

            return generated_text

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout after {self.timeout}s")
            raise RuntimeError(
                f"LLM generation timeout after {self.timeout}s. "
                f"프롬프트가 너무 길거나 서버 부하가 높을 수 있습니다."
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"llama-server request failed: {e}")
            raise RuntimeError(f"LLM generation failed: {e}")

        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse llama-server response: {e}")
            logger.debug(f"Response: {response.text}")
            raise RuntimeError(f"Invalid response from llama-server: {e}")

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        fallback: Optional[Dict[str, Any]] = None,
        strict: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate JSON output using llama-server API with automatic repair.

        This method uses a two-layer approach for maximum reliability:
        1. Enhanced system prompt that strictly enforces JSON output format
        2. Automatic JSON repair using safe_parse() if output is malformed

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            fallback: Fallback value if JSON parsing completely fails
            strict: If True, raise exception on parse failure (default: True)
            **kwargs: Additional arguments for generate()

        Returns:
            Parsed JSON dictionary

        Raises:
            RuntimeError: If strict=True and JSON parsing fails after repair
        """
        # Layer 1: Enhance system prompt to enforce strict JSON output
        json_enforcement = """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL: JSON OUTPUT REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You MUST respond with ONLY valid JSON.
- NO text before the JSON
- NO text after the JSON
- NO markdown code blocks
- NO explanations
- START with { or [
- END with } or ]
- MUST be valid, parseable JSON"""

        json_system_prompt = (system_prompt or "") + json_enforcement

        # Generate output with enhanced prompt
        output = self.generate(prompt, system_prompt=json_system_prompt, **kwargs)

        logger.debug(f"Raw LLM output (first 200 chars): {output[:200]}")

        # Layer 2: Use safe_parse with automatic repair
        try:
            result = safe_parse(output, fallback=fallback, strict=strict)
            logger.info("JSON parsed successfully from LLM output")
            return result

        except ValueError as e:
            logger.error(f"JSON parsing failed even after repair: {e}")
            logger.debug(f"Full output: {output}")

            if strict:
                raise RuntimeError(
                    f"Failed to parse JSON from LLM output even after repair.\n"
                    f"Error: {e}\n"
                    f"Output preview: {output[:500]}..."
                )

            # Return fallback if not strict
            return fallback or {}

    def is_server_ready(self) -> bool:
        """Check if llama-server is ready to accept requests.

        Returns:
            True if server is ready, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.server_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_server_info(self) -> Dict[str, Any]:
        """Get information about the llama-server.

        Returns:
            Server information dictionary
        """
        try:
            response = self.session.get(
                f"{self.server_url}/props",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get server info: {e}")
            return {}

    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'session'):
            self.session.close()
