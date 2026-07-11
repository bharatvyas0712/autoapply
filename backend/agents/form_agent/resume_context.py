from typing import Dict, Any

class ResumeContext:
    """
    Builds context text block out of the parsed user profile and resume data
    to cleanly present to the answer generator.
    """
    
    @staticmethod
    def build_context(profile: Dict[str, Any]) -> str:
        ctx = []
        ctx.append(f"Name: {profile.get('first_name', '')} {profile.get('last_name', '')}")
        ctx.append(f"Headline: {profile.get('headline', '')}")
        ctx.append(f"Summary: {profile.get('summary', '')}")
        
        # Skills
        skills = profile.get("skills", {})
        if isinstance(skills, dict):
            extracted = skills.get("ai_extracted", {})
            if extracted:
                for cat, list_skills in extracted.items():
                    ctx.append(f"{cat.title()}: {', '.join(list_skills)}")
            else:
                ctx.append(f"Skills: {', '.join(skills.get('ai_keywords', []))}")
                
        # Experience
        history = profile.get("work_history", [])
        if isinstance(history, list) and history:
            ctx.append("Work Experience:")
            for idx, job in enumerate(history):
                ctx.append(f"- Job {idx+1}: {job.get('role')} at {job.get('company')} ({job.get('duration')}). Description: {job.get('desc')}")
                
        # Education
        edu = profile.get("education", [])
        if isinstance(edu, list) and edu:
            ctx.append("Education:")
            for e in edu:
                ctx.append(f"- {e.get('degree')} from {e.get('school')} (Graduation: {e.get('year')})")
                
        return "\n".join(ctx)
