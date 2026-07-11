from playwright.async_api import Page
from utilities.logger import get_logger
from utilities.retry import async_retry

logger = get_logger("ActionExecutor")


class ActionExecutor:
    """
    Wraps low-level Playwright interactions with retry logic and logging.
    """

    @staticmethod
    @async_retry(max_retries=3, base_delay=0.5)
    async def click(page: Page, selector: str):
        logger.info(f"Clicking: {selector}")
        await page.click(selector, timeout=15000)

    @staticmethod
    @async_retry(max_retries=3, base_delay=0.5)
    async def click_element(element):
        logger.info("Clicking element directly")
        await element.click(timeout=15000)

    @staticmethod
    @async_retry(max_retries=2, base_delay=0.5)
    async def fill(page: Page, selector: str, value: str):
        logger.info(f"Filling: {selector} = {value[:30]}...")
        await page.fill(selector, value, timeout=10000)

    @staticmethod
    @async_retry(max_retries=2, base_delay=0.5)
    async def select_dropdown(page: Page, selector: str, value: str):
        logger.info(f"Selecting dropdown: {selector} -> {value}")
        await page.select_option(selector, value, timeout=10000)

    @staticmethod
    @async_retry(max_retries=2, base_delay=0.5)
    async def check(page: Page, selector: str):
        logger.info(f"Checking: {selector}")
        await page.check(selector, timeout=10000)

    @staticmethod
    @async_retry(max_retries=3, base_delay=1.0)
    async def navigate(page: Page, url: str):
        logger.info(f"Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

    @staticmethod
    @async_retry(max_retries=2, base_delay=0.5)
    async def upload_file(page: Page, selector: str, file_path: str):
        logger.info(f"Uploading file: {file_path} to {selector}")
        await page.set_input_files(selector, file_path, timeout=15000)

    @staticmethod
    async def type_text(page: Page, selector: str, text: str, delay: int = 50):
        logger.info(f"Typing into {selector}: {text[:30]}...")
        await page.type(selector, text, delay=delay)

    @staticmethod
    async def wait_for_navigation(page: Page, timeout: int = 30000):
        await page.wait_for_load_state("domcontentloaded", timeout=timeout)
