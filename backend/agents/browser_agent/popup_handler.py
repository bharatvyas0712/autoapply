from playwright.async_api import Page
from utilities.logger import get_logger

logger = get_logger("PopupHandler")

POPUP_SELECTORS = [
    # Cookie banners
    "button:has-text('Accept')",
    "button:has-text('Accept all')",
    "button:has-text('Accept cookies')",
    "button:has-text('Got it')",
    "button:has-text('I agree')",
    "button[id*='cookie']",
    "a[id*='cookie']",
    # Newsletter / chat / generic overlay dismiss buttons
    "button:has-text('No thanks')",
    "button:has-text('Close')",
    "button:has-text('Dismiss')",
    "button[aria-label='Close']",
    "button[aria-label='Dismiss']",
    # Generic X icons
    "div[class*='overlay'] button",
    "div[class*='modal'] button[class*='close']",
]


class PopupHandler:
    """
    Dismisses common overlays: cookie banners, newsletter popups, chat widgets, ads.
    Runs as a quick sweep before each major step.
    """

    @staticmethod
    async def dismiss_all(page: Page):
        dismissed = 0
        for selector in POPUP_SELECTORS:
            try:
                elements = await page.query_selector_all(selector)
                for el in elements:
                    if await el.is_visible():
                        await el.click(timeout=3000)
                        dismissed += 1
            except Exception:
                pass  # Element disappeared or click failed — that's fine
        if dismissed:
            logger.info(f"Dismissed {dismissed} popup(s).")
