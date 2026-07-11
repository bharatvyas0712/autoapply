from state import AgentState
from utilities.logger import get_logger

logger = get_logger("InterruptHandler")

class InterruptHandler:
    """
    Handles checkpoints and condition checks that yield or pause orchestrator executions.
    """
    
    @staticmethod
    def handle_interruptions(state: AgentState) -> str:
        status = state.get("status", "running")
        if status == "paused_login":
            logger.warning("Agent execution suspended: User Login Required.")
            return "paused_login"
        elif status == "paused_captcha":
            logger.warning("Agent execution suspended: CAPTCHA Solver Required.")
            return "paused_captcha"
        elif status == "paused_review":
            logger.warning("Agent execution suspended: Form Question Approval Queue Triage.")
            return "paused_review"
            
        return "continue"
