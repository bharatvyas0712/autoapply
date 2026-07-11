from typing import Dict, Any
from config import settings
from utilities.logger import get_logger

logger = get_logger("LLMAnalyzer")

def analyze_with_llm(job_desc: str, resume_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optional LLM step for deep qualitative analysis.
    If an LLM is configured (e.g. OPENAI_API_KEY), this would hit the API.
    For now, it returns empty dict if disabled.
    """
    if not settings.ENABLE_LLM_ANALYSIS or not settings.OPENAI_API_KEY:
        return {}
        
    logger.info("Running deep LLM analysis (Mocked).")
    return {
        "summary": "This job strongly aligns with your backend skills.",
        "strengths": ["Python expertise", "Cloud architecture"],
        "weaknesses": ["Lacks direct experience with specific CI/CD tool mentioned"],
        "application_recommendation": "Highly recommended to apply.",
        "interview_probability": "High"
    }
