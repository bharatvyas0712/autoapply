from typing import Optional
from playwright.async_api import Page, BrowserContext
from browser_manager import browser_manager
from utilities.logger import get_logger

logger = get_logger("TabManager")


class TabManager:
    """
    Manages individual browser tabs (pages) within the active context.
    """

    def __init__(self):
        self._tabs: dict[str, Page] = {}  # label -> Page

    async def open_tab(self, label: str, url: Optional[str] = None) -> Page:
        ctx = await browser_manager.get_context()
        page = await ctx.new_page()
        if url:
            await page.goto(url, wait_until="domcontentloaded")
        self._tabs[label] = page
        logger.info(f"Tab '{label}' opened" + (f" at {url}" if url else ""))
        return page

    async def get_tab(self, label: str) -> Optional[Page]:
        return self._tabs.get(label)

    async def close_tab(self, label: str):
        page = self._tabs.pop(label, None)
        if page and not page.is_closed():
            await page.close()
            logger.info(f"Tab '{label}' closed.")

    async def close_all(self):
        for label in list(self._tabs.keys()):
            await self.close_tab(label)


tab_manager = TabManager()
