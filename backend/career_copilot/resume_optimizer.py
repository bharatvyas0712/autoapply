from typing import Dict, Any, List

from llm_client import generate_json


class ResumeOptimizer:
    """
    Optimizes resume structure, adding action verbs, missing skills,
    and calculating ATS score improvements.
    """

    @staticmethod
    def optimize(resume_text: str, target_keywords: List[str]) -> Dict[str, Any]:
        resume_lower = resume_text.lower()
        missing = [kw for kw in target_keywords if kw.lower() not in resume_lower]

        suggestions = ResumeOptimizer._suggestions(resume_text, target_keywords, missing)

        optimized_text = resume_text + "\n\n[Optimized Section]\nCore Skills: " + ", ".join(target_keywords)

        return {
            "optimized_text": optimized_text,
            "suggestions": suggestions,
            "missing_keywords": missing,
        }

    @staticmethod
    def _suggestions(resume_text: str, target_keywords: List[str], missing: List[str]) -> List[str]:
        prompt = f"""You are a resume coach. Review this resume against the target keywords \
"{', '.join(target_keywords)}" and give 3-5 specific, actionable improvement suggestions based on what \
is actually written (weak phrasing, missing metrics, missing keywords, structure issues). Do not give \
generic advice - reference actual content from the resume where possible.

RESUME:
{resume_text}

Respond with ONLY a JSON array of strings (no markdown fences)."""
        result = generate_json(prompt)
        if isinstance(result, list) and result and all(isinstance(s, str) for s in result):
            return result

        suggestions = [
            "Incorporate more strong action verbs like 'Architected', 'Spearheaded', 'Optimized'.",
        ]
        if missing:
            suggestions.append(f"Add missing keywords: {', '.join(missing)} to increase matching hit-rates.")
        return suggestions