"""
Debug logger module for error tracking and diagnostics.
Saves error logs and screenshots to the debug directory.
"""
import os
import traceback
from datetime import datetime
from pathlib import Path
import json


DEBUG_DIR = Path("debug")


def save_error_log(exception: Exception, context: dict = None, page=None):
    """
    Saves the exception details and context to a file in the debug directory.

    Args:
        exception: The exception that occurred
        context: Additional context information (dict)
        page: Playwright Page object for screenshot capture (optional)
    """
    # Ensure debug directory exists
    DEBUG_DIR.mkdir(exist_ok=True)

    # Generate timestamp and error type
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_type = type(exception).__name__

    # Create log filename
    log_filename = f"error_{timestamp}_{error_type}.txt"
    log_path = DEBUG_DIR / log_filename

    # Prepare log content
    log_content = []
    log_content.append("=" * 80)
    log_content.append(f"ERROR LOG - {datetime.now().isoformat()}")
    log_content.append("=" * 80)
    log_content.append("")

    # Error information
    log_content.append(f"Error Type: {error_type}")
    log_content.append(f"Error Message: {str(exception)}")
    log_content.append("")

    # Context information
    if context:
        log_content.append("Context:")
        log_content.append("-" * 40)
        try:
            log_content.append(json.dumps(context, indent=2, ensure_ascii=False))
        except Exception as e:
            log_content.append(f"Context (repr): {repr(context)}")
            log_content.append(f"(Failed to serialize context: {e})")
        log_content.append("")

    # Full traceback
    log_content.append("Traceback:")
    log_content.append("-" * 40)
    log_content.append(traceback.format_exc())
    log_content.append("")

    # Screenshot information
    screenshot_path = None
    if page:
        try:
            screenshot_filename = f"screenshot_{timestamp}_{error_type}.png"
            screenshot_path = DEBUG_DIR / screenshot_filename
            page.screenshot(path=str(screenshot_path))
            log_content.append(f"Screenshot saved: {screenshot_filename}")
            log_content.append("")
        except Exception as screenshot_error:
            log_content.append(f"Failed to capture screenshot: {screenshot_error}")
            log_content.append("")

    # Write log file
    log_content.append("=" * 80)
    log_path.write_text("\n".join(log_content), encoding="utf-8")

    # Print summary to console
    print(f"🐛 Debug log saved: {log_filename}")
    if screenshot_path and screenshot_path.exists():
        print(f"📸 Screenshot saved: {screenshot_path.name}")

    return str(log_path)
