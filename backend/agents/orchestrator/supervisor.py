from state import AgentState
from utilities.logger import get_logger

logger = get_logger("Supervisor")

class SupervisorAgent:
    """
    Supervisor Agent that coordinates execution flow and decides which node to execute next.
    Acts as a state machine router.
    """
    
    @staticmethod
    def evaluate(state: AgentState) -> str:
        logger.info(f"Evaluating state. Status: {state.get('status')}")
        
        # 1. Check for pause requests
        status = state.get("status", "running")
        if status.startswith("paused"):
            return "pause"
            
        # 2. Check pipeline execution progress
        if not state.get("resume_summary"):
            return "resume_intelligence"
            
        if not state.get("search_results"):
            return "job_search"
            
        if not state.get("matched_jobs"):
            return "job_matching"
            
        # If we have matched jobs, we iterate through them
        if state.get("matched_jobs") and not state.get("current_job"):
            return "select_next_job"
            
        if state.get("current_job") and state.get("status") == "running":
            return "browser_automation"
            
        return "end"
