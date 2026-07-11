from typing import List, Dict, Any

class LearningRecommender:
    """
    Supplies resources (books, courses) matching missing skill requirements.
    """
    
    @staticmethod
    def get_recommendations(missing_skills: List[str]) -> List[Dict[str, Any]]:
        recs = []
        for skill in missing_skills:
            recs.append({
                "skill": skill,
                "resources": [
                    {"type": "course", "title": f"Complete {skill} Bootcamp", "url": "https://udemy.com"},
                    {"type": "doc", "title": f"Official {skill} Documentation", "url": f"https://{skill.lower()}.org"}
                ]
            })
        return recs
