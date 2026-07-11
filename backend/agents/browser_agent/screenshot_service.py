import os
from playwright.async_api import Page
from browser_config import BrowserConfig
from utilities.logger import get_logger
from utilities.helpers import generate_screenshot_filename

logger = get_logger("ScreenshotService")


class ScreenshotService:
    """
    Captures full-page screenshots at key stages of the application workflow
    and stores them on disk. Paths are persisted to the database by the caller.
    """

    @staticmethod
    async def capture(page: Page, job_id: int, stage: str) -> str:
        """
        Takes a screenshot.  Returns the absolute file path.
        stage: before_apply | before_submit | after_submit | error
        """
        filename = generate_screenshot_filename(job_id, stage)
        filepath = os.path.join(BrowserConfig.SCREENSHOTS_DIR, filename)
        await page.screenshot(path=filepath, full_page=True)
        logger.info(f"Screenshot saved: {filepath}")
        return filepath
