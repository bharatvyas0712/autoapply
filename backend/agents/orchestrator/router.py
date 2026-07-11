from state import AgentState
from config import settings

class WorkflowRouter:
    """
    Decides routing logic for conditional edges within the LangGraph StateGraph.
    """
    
    @staticmethod
    def route_match_decision(state: AgentState) -> str:
        current_job = state.get("current_job")
        if not current_job:
            return "select_next_job"
            
        score = current_job.get("match_score", 0)
        if score < settings.MATCH_SCORE_THRESHOLD:
            return "skip_job"
            
        return "browser_automation"

    @staticmethod
    def route_browser_execution(state: AgentState) -> str:
        status = state.get("status", "running")
        if status == "paused_login":
            return "login_wait_node"
        if status == "paused_captcha":
            return "captcha_wait_node"
        if status == "paused_review":
            return "form_review_wait_node"
        if status == "completed":
            return "select_next_job"
        if status == "failed":
            return "select_next_job"
            
        return "browser_automation"
