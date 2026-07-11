from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright
from browser_config import BrowserConfig
from utilities.logger import get_logger

logger = get_logger("BrowserManager")


class BrowserManager:
    """
    Manages the Playwright browser lifecycle.
    Launches a persistent context to keep cookies / sessions alive across runs.
    """

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def launch(self) -> BrowserContext:
        """Launches or returns an existing persistent browser context."""
        if self._context:
            return self._context

        logger.info(f"Launching Playwright ({BrowserConfig.BROWSER_TYPE}, headless={BrowserConfig.HEADLESS})")
        self._playwright = await async_playwright().start()

        launcher = getattr(self._playwright, BrowserConfig.BROWSER_TYPE, self._playwright.chromium)

        launch_kwargs = dict(
            user_data_dir=BrowserConfig.USER_DATA_DIR,
            headless=BrowserConfig.HEADLESS,
            accept_downloads=True,
            viewport={"width": 1280, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ] + (
                [f"--profile-directory={BrowserConfig.PROFILE_DIRECTORY}"]
                if getattr(BrowserConfig, "PROFILE_DIRECTORY", None)
                else []
            ),
        )

        channel = getattr(BrowserConfig, "CHANNEL", None)
        try:
            if channel:
                self._context = await launcher.launch_persistent_context(channel=channel, **launch_kwargs)
            else:
                self._context = await launcher.launch_persistent_context(**launch_kwargs)
        except Exception as e:
            # Chrome channel not available — fall back to bundled Chromium.
            logger.warning(f"Launch with channel={channel!r} failed ({e}); falling back to bundled Chromium.")
            self._context = await launcher.launch_persistent_context(**launch_kwargs)

        # Set default timeouts
        self._context.set_default_navigation_timeout(BrowserConfig.NAVIGATION_TIMEOUT_MS)
        self._context.set_default_timeout(BrowserConfig.ACTION_TIMEOUT_MS)

        logger.info("Browser context launched successfully.")
        return self._context

    async def get_context(self) -> BrowserContext:
        if not self._context:
            return await self.launch()
        return self._context

    async def close(self):
        if self._context:
            await self._context.close()
            self._context = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser closed.")

    @property
    def is_running(self) -> bool:
        return self._context is not None


# Singleton
browser_manager = BrowserManager()