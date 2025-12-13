import os
import traceback
import datetime
import json
from pathlib import Path

DEBUG_DIR = Path("debug")

async def save_error_log(exception: Exception, context: dict = None, page=None):
    """
    Saves the exception details and context to a file in the debug directory.
    If 'page' (Playwright Page) is provided, takes a screenshot.
    
    Args:
        exception (Exception): The exception that occurred.
        context (dict): Additional context data (e.g., request payload).
        page: Playwright Page object (optional).
    """
    try:
        # Create debug directory if it doesn't exist
        if not DEBUG_DIR.exists():
            DEBUG_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        error_type = type(exception).__name__
        filename_base = f"error_{timestamp}_{error_type}"
        file_path = DEBUG_DIR / f"{filename_base}.txt"

        # Take screenshot if page is provided
        screenshot_path = None
        if page:
            try:
                screenshot_filename = f"{filename_base}.png"
                screenshot_path = DEBUG_DIR / screenshot_filename
                await page.screenshot(path=str(screenshot_path), full_page=False)
            except Exception as ss_error:
                print(f"Failed to capture screenshot: {ss_error}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
            f.write(f"Error Type: {error_type}\n")
            f.write(f"Error Message: {str(exception)}\n")
            f.write("\n=== Context ===\n")
            if context:
                try:
                    f.write(json.dumps(context, indent=2, ensure_ascii=False))
                except Exception as json_error:
                    f.write(f"Could not serialize context: {context}\nError: {json_error}")
            else:
                f.write("No context provided.\n")
            
            if screenshot_path:
                f.write(f"\nScreenshot saved to: {screenshot_path}\n")

            f.write("\n\n=== Traceback ===\n")
            f.write(traceback.format_exc())
            
    except Exception as log_error:
        print(f"Failed to save error log: {log_error}")
        traceback.print_exc()
