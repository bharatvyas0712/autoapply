from typing import Dict, Any

class ContextBuilder:
    """
    Builds context text summaries including resumes, jobs, and histories
    to append as system instructions before provider forwarding.
    """
    
    @staticmethod
    def build_system_context(user_profile: dict) -> str:
        ctx = [
            "You are AutoJobApply's AI agent, helping a candidate with their job search "
            "(searching jobs, analyzing resumes, matching, cover letters, applications, scheduling).",
            f"Active User: {user_profile.get('name', 'N/A')}",
            "You have tools available for job-search tasks. Only call a tool when the user's "
            "message actually requires one (e.g. 'find me jobs', 'check my resume'). "
            "For greetings, small talk, or general questions, just reply normally in plain text - "
            "do not call a tool and do not refuse.",
        ]
        return "\n".join(ctx)