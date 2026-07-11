import os
from playwright.async_api import Page, Download
from browser_config import BrowserConfig
from utilities.logger import get_logger
from utilities.helpers import sanitize_filename

logger = get_logger("DownloadManager")


class DownloadManager:
    """
    Handles file downloads triggered by the browser (confirmation PDFs, receipts).
    """

    @staticmethod
    async def handle_download(download: Download) -> str:
        suggested = download.suggested_filename or "download.pdf"
        safe_name = sanitize_filename(suggested)
        dest = os.path.join(BrowserConfig.DOWNLOADS_DIR, safe_name)
        await download.save_as(dest)
        logger.info(f"Download saved: {dest}")
        return dest

    @staticmethod
    async def save_page_as_pdf(page: Page, job_id: int) -> str:
        """Saves the current page as a PDF (only works in Chromium headless mode)."""
        filename = f"confirmation_job_{job_id}.pdf"
        dest = os.path.join(BrowserConfig.DOWNLOADS_DIR, filename)
        try:
            await page.pdf(path=dest)
            logger.info(f"Page PDF saved: {dest}")
        except Exception as e:
            logger.warning(f"PDF save failed (headless-only feature): {e}")
            dest = ""
        return dest
