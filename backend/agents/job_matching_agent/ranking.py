from typing import Dict, Any

def compute_overall_rank(scores: Dict[str, float]) -> float:
    """
    Computes a weighted overall match score (0-100).
    Weights:
    Semantic Score: 40%
    Skill Score: 30%
    Experience Score: 15%
    Location Score: 10%
    Education Score: 5%
    """
    sem = scores.get('semantic_score', 0) * 0.40
    skill = scores.get('skill_score', 0) * 0.30
    exp = scores.get('experience_score', 0) * 0.15
    loc = scores.get('location_score', 0) * 0.10
    edu = scores.get('education_score', 0) * 0.05
    
    overall = sem + skill + exp + loc + edu
    return min(max(overall, 0.0), 100.0)
