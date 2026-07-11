from typing import Optional, Dict
from playwright.async_api import BrowserContext
from browser_manager import browser_manager
from utilities.logger import get_logger
from utilities.helpers import generate_session_id

logger = get_logger("SessionManager")


class SessionManager:
    """
    Manages browser sessions — tracks which user owns the current session,
    stores cookies, and enables session reuse across application runs.
    """

    def __init__(self):
        self._sessions: Dict[str, dict] = {}  # session_id -> metadata

    async def create_session(self, user_id: int) -> str:
        ctx = await browser_manager.launch()
        sid = generate_session_id()
        self._sessions[sid] = {
            "user_id": user_id,
            "status": "running",
        }
        logger.info(f"Session {sid} created for user {user_id}")
        return sid

    def get_session(self, session_id: str) -> Optional[dict]:
        return self._sessions.get(session_id)

    def update_status(self, session_id: str, status: str):
        if session_id in self._sessions:
            self._sessions[session_id]["status"] = status

    async def close_session(self, session_id: str):
        if session_id in self._sessions:
            self._sessions[session_id]["status"] = "stopped"
            logger.info(f"Session {session_id} stopped.")

    @property
    def active_sessions(self):
        return {k: v for k, v in self._sessions.items() if v["status"] == "running"}


session_manager = SessionManager()
