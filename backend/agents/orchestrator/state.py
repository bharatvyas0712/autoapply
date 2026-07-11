from typing import TypedDict, Dict, Any, List, Optional

class AgentState(TypedDict):
    """
    Shared strongly-typed state dict across the multi-agent orchestrator.
    """
    user_id: int
    session_id: int
    
    # Resume Info
    resume_path: Optional[str]
    resume_text: Optional[str]
    resume_summary: Optional[str]
    skills: List[str]
    keywords: List[str]
    
    # Search & Match Jobs
    search_results: List[Dict[str, Any]]
    matched_jobs: List[Dict[str, Any]]
    
    # Current Execution State
    current_job: Optional[Dict[str, Any]]
    current_page: Optional[str]
    application_progress: float
    generated_answers: Dict[str, str]
    
    # Controls / Tracing
    status: str  # running, paused_captcha, paused_login, paused_review, completed, failed
    errors: List[str]
    logs: List[str]
    
    # Router Decision Routing
    next_step: Optional[str]