from playwright.async_api import Page
from utilities.logger import get_logger

logger = get_logger("LoginHandler")

LOGIN_SELECTORS = [
    "input[type='password']",
    "form[action*='login']",
    "form[action*='signin']",
    "a[href*='login']",
    "button:has-text('Sign in')",
    "button:has-text('Log in')",
]


class LoginHandler:
    """
    Detects login / authentication walls.
    NEVER fills credentials — pauses and lets the user log in manually.
    """

    @staticmethod
    async def detect(page: Page) -> bool:
        for selector in LOGIN_SELECTORS:
            try:
                el = await page.query_selector(selector)
                if el and await el.is_visible():
                    logger.warning(f"Login wall detected via: {selector}")
                    return True
            except Exception:
                pass
        return False

    @staticmethod
    async def wait_until_logged_in(page: Page, timeout_sec: int = 300):
        """Polls until the login wall disappears (user has authenticated)."""
        import asyncio
        elapsed = 0
        while elapsed < timeout_sec:
            still_login = await LoginHandler.detect(page)
            if not still_login:
                logger.info("User appears to have logged in.")
                return True
            await asyncio.sleep(3)
            elapsed += 3
        logger.error("Login timeout — user did not log in in time.")
        return False
