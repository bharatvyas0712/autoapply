from typing import Dict, Any

class CompanyAnalyzer:
    """
    Supplies company overview, culture insights, and tech stacks.
    """
    
    @staticmethod
    def analyze(company_name: str) -> Dict[str, Any]:
        return {
            "company": company_name,
            "culture": "Fast-paced, engineering-led, highly collaborative.",
            "tech_stack": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
            "interview_process": "1 Phone Screen -> 1 Take Home Coding -> 2 Panels -> Offer"
        }
