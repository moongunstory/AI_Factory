"""
LLM Client for local Llama model communication.

Provides a clean HTTP interface to the local Llama server that exposes
an OpenAI-compatible Chat Completions API.
"""

import logging
from typing import Any

import requests
from requests.exceptions import RequestException, Timeout

from shorts_llm.config import (
    LOCAL_LLM_BASE_URL,
    DEFAULT_MODEL_NAME,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================


class LLMClientError(Exception):
    """Base exception for LLM client errors."""
    pass


class LLMConnectionError(LLMClientError):
    """Raised when unable to connect to the LLM server."""
    pass


class LLMResponseError(LLMClientError):
    """Raised when the LLM returns an invalid or error response."""
    pass


class InvalidLLMResponse(LLMClientError):
    """Raised when the LLM response doesn't match expected format."""
    pass


# ============================================================================
# LLM Client Functions
# ============================================================================


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL_NAME,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    base_url: str | None = None,
) -> str:
    """
    Call the local Llama Chat Completions API.

    Args:
        system_prompt: System message that sets context/role for the LLM
        user_prompt: User message with the actual task/question
        model: Model identifier (default: local-llama-3.1-8b-instruct)
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens to generate
        base_url: Override the base URL from config/env

    Returns:
        The assistant's response content as a string

    Raises:
        LLMConnectionError: If unable to connect to the server
        LLMResponseError: If the server returns an error
        InvalidLLMResponse: If the response format is invalid

    Example:
        >>> response = chat_completion(
        ...     system_prompt="You are a helpful assistant.",
        ...     user_prompt="What is 2+2?"
        ... )
        >>> print(response)
        "4"
    """
    if base_url is None:
        base_url = LOCAL_LLM_BASE_URL

    endpoint = f"{base_url.rstrip('/')}/chat/completions"

    # Build the request payload (OpenAI-compatible format)
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    logger.debug(f"Sending chat completion request to {endpoint}")
    logger.debug(f"Model: {model}, Temperature: {temperature}, Max tokens: {max_tokens}")

    try:
        response = requests.post(
            endpoint,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

    except Timeout as e:
        error_msg = f"Request to LLM server timed out after {REQUEST_TIMEOUT}s: {endpoint}"
        logger.error(error_msg)
        raise LLMConnectionError(error_msg) from e

    except RequestException as e:
        error_msg = f"Failed to connect to LLM server at {endpoint}: {e}"
        logger.error(error_msg)
        raise LLMConnectionError(error_msg) from e

    # Parse the response
    try:
        response_data = response.json()
    except ValueError as e:
        error_msg = "LLM server returned invalid JSON"
        logger.error(f"{error_msg}: {response.text[:500]}")
        raise InvalidLLMResponse(error_msg) from e

    # Validate response structure (OpenAI-compatible format)
    if "choices" not in response_data:
        error_msg = "LLM response missing 'choices' field"
        logger.error(f"{error_msg}: {response_data}")
        raise InvalidLLMResponse(error_msg)

    if not response_data["choices"]:
        error_msg = "LLM response has empty 'choices' array"
        logger.error(f"{error_msg}: {response_data}")
        raise InvalidLLMResponse(error_msg)

    choice = response_data["choices"][0]

    if "message" not in choice:
        error_msg = "LLM response choice missing 'message' field"
        logger.error(f"{error_msg}: {choice}")
        raise InvalidLLMResponse(error_msg)

    if "content" not in choice["message"]:
        error_msg = "LLM response message missing 'content' field"
        logger.error(f"{error_msg}: {choice['message']}")
        raise InvalidLLMResponse(error_msg)

    content = choice["message"]["content"]

    if not isinstance(content, str):
        error_msg = f"LLM response content is not a string: {type(content)}"
        logger.error(error_msg)
        raise InvalidLLMResponse(error_msg)

    logger.debug(f"Received response: {len(content)} characters")
    return content


def chat_completion_json(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL_NAME,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    base_url: str | None = None,
) -> dict[str, Any]:
    """
    Call the LLM and parse the response as JSON.

    This is a convenience wrapper around chat_completion() that automatically
    parses the response as JSON and validates it.

    Args:
        system_prompt: System message
        user_prompt: User message (should request JSON output)
        model: Model identifier
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        base_url: Override the base URL

    Returns:
        Parsed JSON response as a dictionary

    Raises:
        LLMConnectionError: If unable to connect
        LLMResponseError: If the server returns an error
        InvalidLLMResponse: If response is not valid JSON

    Example:
        >>> result = chat_completion_json(
        ...     system_prompt="You output JSON only.",
        ...     user_prompt="Generate a JSON object with a 'name' field."
        ... )
        >>> print(result['name'])
    """
    import json

    content = chat_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        base_url=base_url,
    )

    # Try to extract JSON from markdown code blocks if present
    content_stripped = content.strip()

    if content_stripped.startswith("```json"):
        # Extract JSON from markdown code block
        try:
            start = content_stripped.index("```json") + 7
            end = content_stripped.rindex("```")
            content_stripped = content_stripped[start:end].strip()
        except ValueError:
            pass  # No valid code block, try parsing as-is

    elif content_stripped.startswith("```"):
        # Generic code block
        try:
            start = content_stripped.index("```") + 3
            end = content_stripped.rindex("```")
            content_stripped = content_stripped[start:end].strip()
        except ValueError:
            pass

    try:
        return json.loads(content_stripped)

    except json.JSONDecodeError as e:
        error_msg = f"LLM response is not valid JSON: {e}"
        logger.error(f"{error_msg}\nResponse preview: {content[:500]}")
        raise InvalidLLMResponse(error_msg) from e


def test_connection(base_url: str | None = None) -> bool:
    """
    Test the connection to the local LLM server.

    Args:
        base_url: Override the base URL from config/env

    Returns:
        True if connection successful, False otherwise

    Example:
        >>> if test_connection():
        ...     print("LLM server is reachable")
    """
    try:
        chat_completion(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'OK' if you can hear me.",
            max_tokens=10,
            base_url=base_url,
        )
        logger.info("LLM server connection test successful")
        return True

    except LLMClientError as e:
        logger.warning(f"LLM server connection test failed: {e}")
        return False
