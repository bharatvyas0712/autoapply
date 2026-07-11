import asyncio
from typing import Dict, Any
from datetime import datetime, timezone

from browser_manager import browser_manager
from tab_manager import tab_manager
from state_manager import state_manager, ApplicationState
from navigator import Navigator
from action_executor import ActionExecutor
from application_controller import ApplicationController
from captcha_handler import CaptchaHandler
from login_handler import LoginHandler
from popup_handler import PopupHandler
from error_handler import ErrorHandler
from screenshot_service import ScreenshotService
from upload_manager import UploadManager
from utilities.logger import get_logger

logger = get_logger("BrowserAgent")


class BrowserAgent:
    """
    Top-level orchestrator.
    Receives an approved job, drives the full application workflow, and persists results.
    """

    @staticmethod
    async def apply_to_job(
        job_id: int,
        job_url: str,
        form_data: Dict[str, Any],
        resume_path: str,
        cover_letter_path: str = "",
    ) -> Dict[str, Any]:

        state = state_manager.create(job_id)
        state.status = "running"

        try:
            # ── 1. Open page ────────────────────────────────────────
            page = await tab_manager.open_tab(f"job_{job_id}", job_url)
            state.current_page = job_url
            state.advance("open_page")
            await state.wait_if_paused()

            # Dismiss cookie banners etc.
            await PopupHandler.dismiss_all(page)

            # ── 2. Login check ──────────────────────────────────────
            if await LoginHandler.detect(page):
                state.pause("login")
                logger.warning("Waiting for user to log in…")
                await LoginHandler.wait_until_logged_in(page)
                state.resume()

            await state.wait_if_paused()

            # ── 3. CAPTCHA check ────────────────────────────────────
            if await CaptchaHandler.detect(page):
                state.pause("captcha")
                logger.warning("Waiting for user to solve CAPTCHA…")
                await CaptchaHandler.wait_until_solved(page)
                state.resume()

            await state.wait_if_paused()

            # ── 4. Detect ATS type ──────────────────────────────────
            ats_type = ApplicationController.detect_ats(job_url)
            state.advance("detect_ats")

            # ── 5. Screenshot: before_apply ─────────────────────────
            await ScreenshotService.capture(page, job_id, "before_apply")

            # ── 6. Analyze page ─────────────────────────────────────
            forms = await Navigator.detect_forms(page)
            logger.info(f"Detected {len(forms)} form(s) on the page.")
            state.advance("analyze_page")

            # ── 7. Fill forms ───────────────────────────────────────
            await ApplicationController.fill_form(page, form_data, ats_type)
            state.advance("fill_form")
            await state.wait_if_paused()

            # ── 8. Upload resume ────────────────────────────────────
            uploaded = await UploadManager.upload_resume(page, resume_path)
            if uploaded:
                state.advance("upload_resume")
            else:
                logger.warning("Resume upload field not found — skipping.")

            # Upload cover letter if available
            if cover_letter_path:
                await UploadManager.upload_cover_letter(page, cover_letter_path)

            await state.wait_if_paused()

            # ── 9. Navigate multi-step (Next buttons) ───────────────
            for _ in range(10):  # safety cap
                next_btn = await Navigator.find_next_button(page)
                if not next_btn:
                    break
                await ActionExecutor.click_element(next_btn)
                await ActionExecutor.wait_for_navigation(page)
                await PopupHandler.dismiss_all(page)

                # Re-check captcha / login after each step
                if await CaptchaHandler.detect(page):
                    state.pause("captcha")
                    await CaptchaHandler.wait_until_solved(page)
                    state.resume()

            # ── 10. Review ──────────────────────────────────────────
            review_btn = await Navigator.find_review_button(page)
            if review_btn:
                await ActionExecutor.click_element(review_btn)
                await ActionExecutor.wait_for_navigation(page)
            state.advance("review")

            # ── 11. Screenshot: before_submit ───────────────────────
            await ScreenshotService.capture(page, job_id, "before_submit")

            # ── 12. Submit ──────────────────────────────────────────
            submit_btn = await Navigator.find_submit_button(page)
            if submit_btn:
                await ActionExecutor.click_element(submit_btn)
                await ActionExecutor.wait_for_navigation(page)
                state.advance("submit")
                state.status = "submitted"
            else:
                logger.warning("Submit button not found — application may require manual submission.")
                state.status = "failed"
                state.fail("Submit button not found.")

            # ── 13. Screenshot: after_submit ────────────────────────
            await ScreenshotService.capture(page, job_id, "after_submit")

            # ── 14. Close tab ───────────────────────────────────────
            await tab_manager.close_tab(f"job_{job_id}")

            return state.to_dict()

        except Exception as e:
            import traceback
            traceback.print_exc()
            state.fail(str(e))
            state.status = "failed"
            # Try to capture error screenshot
            try:
                page = await tab_manager.get_tab(f"job_{job_id}")
                if page and not page.is_closed():
                    await ScreenshotService.capture(page, job_id, "error")
            except Exception:
                pass
            return state.to_dict()
