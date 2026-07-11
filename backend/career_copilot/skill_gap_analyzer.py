from typing import Dict, Any, List

class SkillGapAnalyzer:
    """
    Maps missing skills and sets priority levels.
    """
    
    @staticmethod
    def analyze(current_skills: List[str], target_job_skills: List[str]) -> Dict[str, Any]:
        curr_set = set(s.lower() for s in current_skills)
        missing = []
        for s in target_job_skills:
            if s.lower() not in curr_set:
                missing.append(s)
                
        # Generate priority tags
        priorities = {}
        for idx, skill in enumerate(missing):
            level = "High" if idx < 2 else "Medium"
            priorities[skill] = {
                "priority": level,
                "estimated_learning_hours": 15 if level == "High" else 30
            }
            
        return {
            "missing_skills": missing,
            "skill_details": priorities
        }
