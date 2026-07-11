from playwright.async_api import Page
from utilities.logger import get_logger

logger = get_logger("ErrorHandler")


class ErrorHandler:
    """
    Handles recoverable browser errors: timeouts, crashed pages, navigation failures.
    """

    @staticmethod
    async def handle_page_crash(page: Page, url: str) -> bool:
        """Attempts to reload the page after a crash."""
        try:
            logger.warning(f"Attempting crash recovery for {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            logger.info("Page recovered successfully.")
            return True
        except Exception as e:
            logger.error(f"Crash recovery failed: {e}")
            return False

    @staticmethod
    async def handle_timeout(page: Page) -> bool:
        """Reloads the current page after a timeout."""
        try:
            logger.warning("Handling timeout — reloading page")
            await page.reload(wait_until="domcontentloaded", timeout=30000)
            return True
        except Exception as e:
            logger.error(f"Timeout recovery failed: {e}")
            return False

    @staticmethod
    async def is_page_alive(page: Page) -> bool:
        try:
            await page.title()
            return True
        except Exception:
            return False
