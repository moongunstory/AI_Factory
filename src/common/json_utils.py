"""JSON parsing utilities with automatic repair for LLM outputs.

This module provides robust JSON parsing that handles malformed JSON
outputs from LLMs by automatically attempting to repair them.

Two-layer approach:
1. Try standard json.loads() first (fast path)
2. On failure, use json_repair to fix and retry (recovery path)
"""
import json
import re
from typing import Dict, Any, Optional
from json_repair import repair_json

from .logger import setup_logger

logger = setup_logger(__name__)


def extract_json_block(text: str) -> str:
    """Extract JSON block from text that may contain other content.

    Handles cases like:
    - "Here's the result: {...}"
    - "```json\n{...}\n```"
    - Plain JSON: "{...}"
    - Text with JSON embedded: "Some text {...} more text"

    Args:
        text: Text that may contain JSON

    Returns:
        Extracted JSON string
    """
    # Remove markdown code blocks (both ```json and ```)
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    # Strategy 1: Find JSON object (between first { and last })
    start_idx = text.find('{')
    end_idx = text.rfind('}')

    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        extracted = text[start_idx:end_idx + 1]
        logger.debug(f"Extracted JSON object (length: {len(extracted)})")
        return extracted

    # Strategy 2: Try array format: [...]
    start_idx = text.find('[')
    end_idx = text.rfind(']')

    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        extracted = text[start_idx:end_idx + 1]
        logger.debug(f"Extracted JSON array (length: {len(extracted)})")
        return extracted

    # Strategy 3: If no JSON markers found, log warning and return as-is
    logger.warning(f"No JSON markers found in text. First 200 chars: {text[:200]}")
    return text


def safe_parse(
    json_text: str,
    fallback: Optional[Dict[str, Any]] = None,
    strict: bool = False
) -> Dict[str, Any]:
    """Parse JSON with automatic repair on failure.

    This function implements a two-layer approach:
    1. Try standard json.loads() (fast path)
    2. On failure, extract JSON block, repair, and retry (recovery path)

    Args:
        json_text: JSON string (possibly malformed)
        fallback: Fallback value if all parsing fails (default: empty dict)
        strict: If True, raise exception on failure instead of using fallback

    Returns:
        Parsed JSON as dictionary

    Raises:
        ValueError: If strict=True and parsing fails

    Examples:
        >>> safe_parse('{"key": "value"}')
        {'key': 'value'}

        >>> safe_parse('{"key": "value",}')  # Trailing comma
        {'key': 'value'}

        >>> safe_parse('Here is the result: {"key": "value"}')
        {'key': 'value'}

        >>> safe_parse('{"key": "missing quote}')
        {'key': 'missing quote'}
    """
    if fallback is None:
        fallback = {}

    # Clean up input
    json_text = json_text.strip()

    if not json_text:
        logger.warning("Empty JSON text provided")
        if strict:
            raise ValueError("Empty JSON text")
        return fallback

    # Layer 1: Try standard json.loads() first (fast path)
    try:
        result = json.loads(json_text)
        logger.debug("JSON parsed successfully (standard parser)")
        return result
    except json.JSONDecodeError as e:
        logger.debug(f"Standard JSON parse failed: {e}")

    # Layer 2: Try to extract and repair JSON
    try:
        # Extract JSON block from surrounding text
        extracted = extract_json_block(json_text)
        logger.debug(f"Extracted JSON block: {extracted[:100]}...")

        # Try parsing extracted JSON
        try:
            result = json.loads(extracted)
            logger.info("JSON parsed successfully after extraction")
            return result
        except json.JSONDecodeError:
            pass

        # Repair the JSON
        repaired = repair_json(extracted)
        logger.debug(f"Repaired JSON: {repaired[:100]}...")

        # Parse repaired JSON
        result = json.loads(repaired)
        logger.info("JSON parsed successfully after repair")
        return result

    except Exception as e:
        logger.error(f"JSON repair failed: {e}")
        logger.debug(f"Original text: {json_text[:200]}...")

        if strict:
            raise ValueError(f"Failed to parse JSON even after repair: {e}")

        logger.warning(f"Using fallback value due to parse failure")
        return fallback


def validate_json_schema(
    data: Dict[str, Any],
    required_keys: list[str],
    strict: bool = False
) -> bool:
    """Validate that JSON contains required keys.

    Args:
        data: Parsed JSON dictionary
        required_keys: List of required key names
        strict: If True, raise exception on missing keys

    Returns:
        True if all required keys present, False otherwise

    Raises:
        ValueError: If strict=True and keys are missing
    """
    missing_keys = [key for key in required_keys if key not in data]

    if missing_keys:
        error_msg = f"Missing required keys: {missing_keys}"
        logger.warning(error_msg)

        if strict:
            raise ValueError(error_msg)

        return False

    return True


def safe_parse_with_schema(
    json_text: str,
    required_keys: list[str],
    fallback: Optional[Dict[str, Any]] = None,
    strict: bool = False
) -> Dict[str, Any]:
    """Parse JSON and validate required keys in one step.

    Args:
        json_text: JSON string (possibly malformed)
        required_keys: List of required key names
        fallback: Fallback value if parsing/validation fails
        strict: If True, raise exception on failure

    Returns:
        Parsed and validated JSON dictionary

    Raises:
        ValueError: If strict=True and parsing/validation fails
    """
    # Parse JSON
    data = safe_parse(json_text, fallback=fallback, strict=strict)

    # Validate schema
    validate_json_schema(data, required_keys, strict=strict)

    return data
