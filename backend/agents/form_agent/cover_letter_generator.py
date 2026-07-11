from typing import Dict, Any

class CoverLetterGenerator:
    """
    Generates tailored, professional cover letters based on profile and target job description.
    """
    
    @staticmethod
    def generate(profile: Dict[str, Any], job_details: Dict[str, Any], length: str = "medium") -> str:
        name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip() or "Applicant"
        email = profile.get("email", "")
        phone = profile.get("phone", "")
        headline = profile.get("headline", "Software Developer")
        
        company = job_details.get("company", "your company")
        title = job_details.get("title", "Software Engineering position")
        
        skills = profile.get("skills", {})
        top_skills = []
        if isinstance(skills, dict):
            top_skills = skills.get("ai_extracted", {}).get("programming_languages", [])[:4]
            if not top_skills:
                top_skills = skills.get("ai_keywords", [])[:4]
        skills_str = ", ".join(top_skills)
        
        salutation = f"Dear Hiring Team at {company},\n\n"
        signoff = f"\n\nSincerely,\n{name}\n{email} | {phone}"
        
        if length == "short":
            body = (
                f"I am writing to express my strong interest in the {title} position at {company}. "
                f"As a {headline} with technical experience in {skills_str}, I am confident in my ability "
                f"to make a meaningful contribution to your engineering team. I look forward to discussing "
                f"how my background aligns with your current needs."
            )
        elif length == "long":
            body = (
                f"I am writing to formally apply for the {title} vacancy at {company}. "
                f"With a solid foundation as a {headline}, I have built my career around designing clean, "
                f"efficient solutions and collaborating with productive product teams. "
                f"My key areas of expertise include hands-on work with {skills_str}. "
                f"What excites me about {company} is your commitment to technical innovation. "
                f"I welcome the opportunity to join your team and contribute immediately to your "
                f"development cycles. Thank you for your time and consideration."
            )
        else:  # medium default
            body = (
                f"I am writing to express my interest in the {title} position at {company}. "
                f"As a {headline} specializing in modern software development, my skills in {skills_str} "
                f"align perfectly with the requirements outlined in your job posting. "
                f"I have a proven track record of solving technical challenges, writing clean code, "
                f"and delivering scalable features on time. I am enthusiastic about the prospect "
                f"of joining {company} and would love to discuss my qualifications further."
            )
            
        return f"{salutation}{body}{signoff}"
