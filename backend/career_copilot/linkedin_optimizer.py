from typing import Dict, Any

class LinkedInOptimizer:
    """
    Creates recruiter-friendly headers and summary blocks.
    """
    
    @staticmethod
    def optimize_profile(skills: list, target_role: str) -> Dict[str, Any]:
        headline = f"{target_role} | Specialized in {', '.join(skills[:3])} | Building scalable systems"
        about = (
            f"Passionate developer targeting {target_role} vacancies. "
            f"Equipped with hands-on expertise in {', '.join(skills)}. "
            "Let's connect!"
        )
        return {
            "headline": headline,
            "about": about,
            "skills": skills
        }
