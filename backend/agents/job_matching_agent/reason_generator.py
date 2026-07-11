from typing import Dict, Any, List

def generate_reason(scores: Dict[str, float], skill_gap: Dict[str, Any], decision: str) -> str:
    """Generates a human-readable explanation for the matching decision."""
    reasons = []
    
    if scores['skill_score'] > 80:
        reasons.append("Strong alignment with required technical skills.")
    elif scores['skill_score'] < 50:
        reasons.append("Missing several core technical skills.")
        
    if scores['semantic_score'] > 80:
        reasons.append("High semantic relevance to your resume profile.")
        
    if scores['experience_score'] < 50:
        reasons.append("Job experience requirements misaligned with your profile.")
        
    if skill_gap.get('critical_missing_skills'):
        crit = ", ".join(skill_gap['critical_missing_skills'][:3])
        reasons.append(f"Missing critical skills: {crit}.")
        
    if decision == "AUTO_APPLY":
        return "Overall highly recommended: " + " ".join(reasons)
    elif decision == "SKIP":
        return "Not recommended: " + " ".join(reasons)
    else:
        return "Review suggested: " + " ".join(reasons)
