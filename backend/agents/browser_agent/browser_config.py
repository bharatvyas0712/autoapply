import os

class BrowserConfig:
    # Use visible mode by default for debugging / manual captcha intervention
    HEADLESS = False
    BROWSER_TYPE = "chromium" # options: chromium, firefox, webkit

    # Use the installed Google Chrome ("chrome" channel) so pages see a real
    # browser. Set to None to use bundled Chromium instead.
    CHANNEL = "chrome"

    # ONE persistent profile shared by every engine in this project so a login
    # done once (in the form filler OR here) is reused everywhere — no re-login.
    # Override with the AUTOJOBAPPLY_PROFILE_DIR env var if needed.
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    USER_DATA_DIR = (
        os.environ.get("AUTOJOBAPPLY_PROFILE_DIR")
        or os.path.join(_PROJECT_ROOT, "browser_profile")
    )
    PROFILE_DIRECTORY = os.environ.get("AUTOJOBAPPLY_PROFILE_DIRECTORY") or None
    
    # Timeouts
    NAVIGATION_TIMEOUT_MS = 60000
    ACTION_TIMEOUT_MS = 30000
    
    # Assets
    DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
    SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
    
    # Ensure dirs exist
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)