from typing import Dict, Any

class FieldClassifier:
    """
    Classifies a form field label/name into canonical categories:
    Personal, Education, Work Experience, Technical Skills, Behavioral, Salary, Documents.
    """
    
    @staticmethod
    def classify(label: str, name: str) -> str:
        text = f"{label} {name}".lower()
        
        # Heuristics
        if any(w in text for w in ["resume", "cv", "portfolio", "cover letter", "attachment", "transcript"]):
            return "Documents"
        if any(w in text for w in ["salary", "compensation", "expectation", "usd", "hourly", "rate"]):
            return "Salary"
        if any(w in text for w in ["school", "university", "college", "degree", "education", "gpa", "major", "graduation"]):
            return "Education"
        if any(w in text for w in ["experience", "company", "employer", "title", "role", "work", "history"]):
            return "Work Experience"
        if any(w in text for w in ["skill", "programming", "languages", "frameworks", "technologies", "tech"]):
            return "Technical Skills"
        if any(w in text for w in ["why", "tell", "describe", "achievement", "describe", "strengths", "weakness"]):
            return "Behavioral Questions"
        if any(w in text for w in ["first name", "last name", "name", "email", "phone", "address", "city", "country", "zip"]):
            return "Personal Information"
            
        return "Behavioral Questions"  # Default fallback to evaluate semantically
