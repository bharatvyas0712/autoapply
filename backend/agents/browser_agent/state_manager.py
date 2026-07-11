import asyncio
from typing import Optional, List
from utilities.logger import get_logger

logger = get_logger("StateManager")


class ApplicationState:
    """Tracks the full lifecycle of a single application attempt."""

    def __init__(self, job_id: int):
        self.job_id = job_id
        self.current_page: str = ""
        self.current_step: str = "init"
        self.completed_steps: List[str] = []
        self.pending_steps: List[str] = [
            "open_page", "detect_ats", "analyze_page",
            "fill_form", "upload_resume", "review", "submit"
        ]
        self.errors: List[str] = []
        self.retry_count: int = 0
        self.status: str = "queued"  # queued, running, paused_captcha, paused_login, submitted, failed

        # Event used for pause / resume
        self._resume_event = asyncio.Event()
        self._resume_event.set()  # starts un-paused

    def advance(self, step_name: str):
        self.current_step = step_name
        if step_name in self.pending_steps:
            self.pending_steps.remove(step_name)
        self.completed_steps.append(step_name)
        logger.info(f"[Job {self.job_id}] Step completed: {step_name}")

    def fail(self, error: str):
        self.errors.append(error)
        self.retry_count += 1
        logger.error(f"[Job {self.job_id}] Error: {error} (retry #{self.retry_count})")

    def pause(self, reason: str):
        self.status = f"paused_{reason}"
        self._resume_event.clear()
        logger.warning(f"[Job {self.job_id}] PAUSED — {reason}")

    def resume(self):
        self.status = "running"
        self._resume_event.set()
        logger.info(f"[Job {self.job_id}] RESUMED")

    async def wait_if_paused(self):
        """Blocks until the state is un-paused."""
        await self._resume_event.wait()

    def to_dict(self):
        return {
            "job_id": self.job_id,
            "current_page": self.current_page,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "pending_steps": self.pending_steps,
            "errors": self.errors,
            "retry_count": self.retry_count,
            "status": self.status,
        }


class StateManager:
    """Registry of all active ApplicationState instances."""

    def __init__(self):
        self._states: dict[int, ApplicationState] = {}

    def create(self, job_id: int) -> ApplicationState:
        state = ApplicationState(job_id)
        self._states[job_id] = state
        return state

    def get(self, job_id: int) -> Optional[ApplicationState]:
        return self._states.get(job_id)

    def remove(self, job_id: int):
        self._states.pop(job_id, None)

    @property
    def all_states(self):
        return {k: v.to_dict() for k, v in self._states.items()}


state_manager = StateManager()
