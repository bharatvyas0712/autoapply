from typing import Dict, Any

from llm_client import generate_json


class CareerPathPlanner:
    """
    Generates 6, 12, and 24-month roadmap schedules.
    """

    @staticmethod
    def generate_roadmaps(current_role: str, target_role: str) -> Dict[str, Any]:
        prompt = f"""You are a career mentor. A person currently working as "{current_role}" wants to \
become a "{target_role}". Create a concrete development roadmap with 2-4 specific, actionable items \
for each timeframe below, tailored to the gap between these two roles.

Respond with ONLY a JSON object in this exact shape (no markdown fences):
{{
  "roadmap_6m": ["...", "..."],
  "roadmap_12m": ["...", "..."],
  "roadmap_24m": ["...", "..."]
}}"""
        result = generate_json(prompt)
        if (
            isinstance(result, dict)
            and all(k in result for k in ("roadmap_6m", "roadmap_12m", "roadmap_24m"))
        ):
            return result

        return CareerPathPlanner._fallback(current_role, target_role)

    @staticmethod
    def _fallback(current_role: str, target_role: str) -> Dict[str, Any]:
        return {
            "roadmap_6m": [
                f"Study the core skills that separate {current_role} from {target_role}.",
                "Take on a stretch project at work that touches those skills.",
            ],
            "roadmap_12m": [
                f"Ship a production project that demonstrates readiness for {target_role}.",
                "Build a portfolio artifact (blog post, OSS contribution, talk) around it.",
            ],
            "roadmap_24m": [
                f"Actively apply and interview for {target_role} positions.",
                "Seek mentorship or a lateral move that puts you closer to the role.",
            ],
        }