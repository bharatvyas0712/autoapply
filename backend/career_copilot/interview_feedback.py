from typing import Dict, Any, List

class InterviewFeedback:
    """
    Compiles detailed scorecards and improvement charts from interview runs.
    """
    
    @staticmethod
    def compile_scorecard(score: float, answers_log: List[Dict[str, str]]) -> Dict[str, Any]:
        return {
            "overall_score": score,
            "evaluation_date": "2026-07-03",
            "sections": {
                "communication": "Strong and clear pacing.",
                "technical_depth": "Demonstrates good framework mechanics."
            },
            "answers_checked": len(answers_log)
        }
