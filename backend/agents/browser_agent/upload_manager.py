from playwright.async_api import Page
from action_executor import ActionExecutor
from navigator import Navigator
from utilities.logger import get_logger

logger = get_logger("UploadManager")


class UploadManager:
    """
    Detects file-upload controls on a page and uploads the resume / cover letter.
    """

    @staticmethod
    async def upload_resume(page: Page, resume_path: str) -> bool:
        upload_fields = await Navigator.detect_upload_fields(page)
        if not upload_fields:
            logger.warning("No upload fields found on page.")
            return False

        # Pick the first visible file input
        for field in upload_fields:
            try:
                if await field.is_visible():
                    await field.set_input_files(resume_path, timeout=15000)
                    logger.info(f"Resume uploaded via file input: {resume_path}")
                    return True
            except Exception as e:
                logger.warning(f"Upload attempt failed: {e}")
        return False

    @staticmethod
    async def upload_cover_letter(page: Page, cover_letter_path: str) -> bool:
        """Attempts to find a second upload field for the cover letter."""
        upload_fields = await Navigator.detect_upload_fields(page)
        if len(upload_fields) < 2:
            logger.info("Only one upload field — cover letter upload skipped.")
            return False

        try:
            await upload_fields[1].set_input_files(cover_letter_path, timeout=15000)
            logger.info(f"Cover letter uploaded: {cover_letter_path}")
            return True
        except Exception as e:
            logger.warning(f"Cover letter upload failed: {e}")
            return False
