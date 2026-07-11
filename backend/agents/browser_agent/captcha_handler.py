from playwright.async_api import Page
from utilities.logger import get_logger

logger = get_logger("CaptchaHandler")

CAPTCHA_SELECTORS = [
    "iframe[src*='recaptcha']",
    "iframe[src*='hcaptcha']",
    "iframe[src*='captcha']",
    "#cf-challenge-running",       # Cloudflare challenge
    ".g-recaptcha",
    ".h-captcha",
    "div[class*='captcha']",
]


class CaptchaHandler:
    """
    Detects CAPTCHA challenges on a page.
    When detected, signals the state machine to pause and notifies the frontend.
    The user must solve the CAPTCHA manually in the visible browser window.
    """

    @staticmethod
    async def detect(page: Page) -> bool:
        for selector in CAPTCHA_SELECTORS:
            try:
                el = await page.query_selector(selector)
                if el and await el.is_visible():
                    logger.warning(f"CAPTCHA detected via selector: {selector}")
                    return True
            except Exception:
                pass
        return False

    @staticmethod
    async def wait_until_solved(page: Page, timeout_sec: int = 300):
        """
        Polls the page every 3 seconds up to `timeout_sec` to see if the CAPTCHA
        is still visible. Returns when it disappears (user solved it).
        """
        import asyncio
        elapsed = 0
        while elapsed < timeout_sec:
            still_present = await CaptchaHandler.detect(page)
            if not still_present:
                logger.info("CAPTCHA appears to be solved.")
                return True
            await asyncio.sleep(3)
            elapsed += 3
        logger.error("CAPTCHA timeout — user did not solve in time.")
        return False
