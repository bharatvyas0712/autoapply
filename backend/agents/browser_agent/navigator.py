from typing import Optional, List, Dict, Any
from playwright.async_api import Page
from utilities.logger import get_logger
from utilities.retry import async_retry

logger = get_logger("Navigator")

# Canonical button labels the agent should recognize on application pages
NEXT_LABELS = ["next", "continue", "proceed", "forward", "save and continue", "save & continue"]
SUBMIT_LABELS = ["submit", "submit application", "apply", "send application", "confirm", "finish"]
REVIEW_LABELS = ["review", "review application", "preview"]
CANCEL_LABELS = ["cancel", "discard", "go back", "previous", "back"]


class Navigator:
    """
    Analyzes a page's DOM to detect interactive elements and navigation buttons.
    """

    @staticmethod
    async def detect_forms(page: Page) -> List[Dict[str, Any]]:
        """Returns metadata for every <form> on the page."""
        forms = await page.query_selector_all("form")
        results = []
        for idx, form in enumerate(forms):
            fields = await Navigator._analyze_form_fields(form)
            results.append({"index": idx, "fields": fields})
        return results

    @staticmethod
    async def _analyze_form_fields(form) -> List[Dict[str, str]]:
        fields = []
        for tag in ["input", "select", "textarea"]:
            elements = await form.query_selector_all(tag)
            for el in elements:
                field_type = await el.get_attribute("type") or tag
                name = await el.get_attribute("name") or ""
                label_text = await el.get_attribute("aria-label") or await el.get_attribute("placeholder") or name
                is_hidden = await el.is_hidden()
                if not is_hidden:
                    fields.append({"tag": tag, "type": field_type, "name": name, "label": label_text})
        return fields

    @staticmethod
    async def find_button(page: Page, labels: List[str]) -> Optional[Any]:
        """Searches for a visible button matching any of the given labels (case-insensitive)."""
        buttons = await page.query_selector_all("button, input[type='submit'], a[role='button']")
        for btn in buttons:
            text = (await btn.inner_text()).strip().lower() if await btn.is_visible() else ""
            if any(lbl in text for lbl in labels):
                return btn
        return None

    @staticmethod
    async def find_next_button(page: Page):
        return await Navigator.find_button(page, NEXT_LABELS)

    @staticmethod
    async def find_submit_button(page: Page):
        return await Navigator.find_button(page, SUBMIT_LABELS)

    @staticmethod
    async def find_review_button(page: Page):
        return await Navigator.find_button(page, REVIEW_LABELS)

    @staticmethod
    async def detect_upload_fields(page: Page) -> List[Any]:
        return await page.query_selector_all("input[type='file']")

    @staticmethod
    async def detect_dropdowns(page: Page) -> List[Any]:
        return await page.query_selector_all("select")

    @staticmethod
    async def detect_checkboxes(page: Page) -> List[Any]:
        return await page.query_selector_all("input[type='checkbox']")

    @staticmethod
    async def detect_radio_buttons(page: Page) -> List[Any]:
        return await page.query_selector_all("input[type='radio']")

    @staticmethod
    async def detect_date_pickers(page: Page) -> List[Any]:
        return await page.query_selector_all("input[type='date'], input[type='datetime-local']")
