from typing import Dict, Any
from playwright.async_api import Page
from utilities.logger import get_logger

logger = get_logger("ApplicationController")

# ── ATS detection patterns ──────────────────────────────────────
ATS_PATTERNS = {
    "greenhouse":       ["greenhouse.io", "boards.greenhouse"],
    "lever":            ["lever.co", "jobs.lever"],
    "workday":          ["myworkdayjobs.com", "wd5.myworkdaysite"],
    "ashby":            ["ashbyhq.com", "jobs.ashby"],
    "oracle":           ["oracle.com/careers", "taleo.net"],
    "successfactors":   ["successfactors.com", "sap.com/careers"],
    "smartrecruiters":  ["smartrecruiters.com"],
    "icims":            ["icims.com"],
    "jobvite":          ["jobvite.com"],
    "linkedin_easy":    ["linkedin.com"],
    "indeed_easy":      ["indeed.com"],
}


class ApplicationController:
    """
    Detects which ATS system a job page belongs to and delegates
    the form-filling strategy accordingly.
    """

    @staticmethod
    def detect_ats(url: str) -> str:
        """Returns the ATS key or 'generic' if unrecognised."""
        url_lower = url.lower()
        for ats_key, patterns in ATS_PATTERNS.items():
            for pattern in patterns:
                if pattern in url_lower:
                    logger.info(f"ATS detected: {ats_key}")
                    return ats_key
        logger.info("No known ATS detected — using generic handler.")
        return "generic"

    @staticmethod
    async def fill_form(page: Page, form_data: Dict[str, Any], ats_type: str):
        """
        Main form-filling router.
        Calls the appropriate ATS-specific strategy.
        Each strategy locates the form fields on the page and fills them.
        """
        if ats_type == "greenhouse":
            await ApplicationController._fill_greenhouse(page, form_data)
        elif ats_type == "lever":
            await ApplicationController._fill_lever(page, form_data)
        elif ats_type == "workday":
            await ApplicationController._fill_workday(page, form_data)
        else:
            await ApplicationController._fill_generic(page, form_data)

    # ── ATS-specific strategies ──────────────────────────────────

    @staticmethod
    async def _fill_greenhouse(page: Page, data: Dict[str, Any]):
        logger.info("Filling Greenhouse application form.")
        await ApplicationController._try_fill(page, "#first_name", data.get("first_name", ""))
        await ApplicationController._try_fill(page, "#last_name", data.get("last_name", ""))
        await ApplicationController._try_fill(page, "#email", data.get("email", ""))
        await ApplicationController._try_fill(page, "#phone", data.get("phone", ""))
        # Greenhouse often has a LinkedIn field
        await ApplicationController._try_fill(page, "input[name*='linkedin']", data.get("linkedin_url", ""))

    @staticmethod
    async def _fill_lever(page: Page, data: Dict[str, Any]):
        logger.info("Filling Lever application form.")
        await ApplicationController._try_fill(page, "input[name='name']", data.get("full_name", ""))
        await ApplicationController._try_fill(page, "input[name='email']", data.get("email", ""))
        await ApplicationController._try_fill(page, "input[name='phone']", data.get("phone", ""))
        await ApplicationController._try_fill(page, "input[name='urls[LinkedIn]']", data.get("linkedin_url", ""))
        await ApplicationController._try_fill(page, "input[name='urls[GitHub]']", data.get("github_url", ""))

    @staticmethod
    async def _fill_workday(page: Page, data: Dict[str, Any]):
        logger.info("Filling Workday application form.")
        await ApplicationController._try_fill(page, "input[data-automation-id='name']", data.get("full_name", ""))
        await ApplicationController._try_fill(page, "input[data-automation-id='email']", data.get("email", ""))
        await ApplicationController._try_fill(page, "input[data-automation-id='phone']", data.get("phone", ""))

    @staticmethod
    async def _fill_generic(page: Page, data: Dict[str, Any]):
        """Best-effort fill for unknown forms using common attribute heuristics."""
        logger.info("Filling generic HTML form.")
        mapping = {
            "first_name": ["first_name", "fname", "first-name", "firstName"],
            "last_name":  ["last_name", "lname", "last-name", "lastName"],
            "email":      ["email", "e-mail", "emailAddress"],
            "phone":      ["phone", "telephone", "mobile", "phoneNumber"],
            "full_name":  ["name", "full_name", "fullName", "applicant_name"],
        }
        for field_key, selectors in mapping.items():
            value = data.get(field_key, "")
            if not value:
                continue
            for s in selectors:
                filled = await ApplicationController._try_fill(page, f"input[name*='{s}']", value)
                if filled:
                    break
                filled = await ApplicationController._try_fill(page, f"input[id*='{s}']", value)
                if filled:
                    break

    @staticmethod
    async def _try_fill(page: Page, selector: str, value: str) -> bool:
        if not value:
            return False
        try:
            el = await page.query_selector(selector)
            if el and await el.is_visible():
                await el.fill(value)
                return True
        except Exception:
            pass
        return False
