class QuestionClassifier:
    """
    Identifies common job application questions.
    """
    
    @staticmethod
    def classify_question(question_text: str) -> str:
        q = question_text.lower()
        
        if any(w in q for w in ["tell us about yourself", "introduce yourself", "about you"]):
            return "ABOUT_SELF"
        if any(w in q for w in ["why should we hire you", "why this role", "why join", "why our company"]):
            return "WHY_HIRE"
        if any(w in q for w in ["strengths", "greatest strength"]):
            return "STRENGTHS"
        if any(w in q for w in ["weakness", "weaknesses"]):
            return "WEAKNESSES"
        if any(w in q for w in ["achievement", "proud"]):
            return "ACHIEVEMENT"
        if any(w in q for w in ["leadership", "led a team"]):
            return "LEADERSHIP"
        if any(w in q for w in ["visa", "sponsorship", "citizen"]):
            return "SPONSORSHIP"
        if any(w in q for w in ["relocate", "relocation"]):
            return "RELOCATION"
        if any(w in q for w in ["expected salary", "salary expectation"]):
            return "SALARY"
            
        return "GENERIC_EXPERIENCE"
