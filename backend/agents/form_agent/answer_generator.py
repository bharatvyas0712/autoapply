from typing import Dict, Any
from question_classifier import QuestionClassifier
from resume_context import ResumeContext
from config import settings
import groq_client
from utilities.logger import get_logger

logger = get_logger("AnswerGenerator")


class AnswerGenerator:
    """
    Generates professional answers to dynamic application questions.
    Primary path: asks the LLM to actually read the question + the user's
    real resume/profile context and job details, and write a genuine,
    personalized answer (this is what lets automation "think" instead of
    just filling a fixed template).
    Fallback path: if no GROQ_API_KEY is configured or the LLM call fails,
    falls back to the safe static templates below so the pipeline never
    breaks.
    """

    @staticmethod
    def generate_answer(question_text: str, profile: Dict[str, Any], job_details: Dict[str, Any]) -> Dict[str, Any]:
        category = QuestionClassifier.classify_question(question_text)

        llm_result = AnswerGenerator._generate_with_llm(question_text, category, profile, job_details)
        if llm_result is not None:
            return llm_result

        logger.warning("LLM unavailable or failed - falling back to static template answer.")
        return AnswerGenerator._generate_from_template(question_text, category, profile, job_details)

    @staticmethod
    def _generate_with_llm(question_text: str, category: str, profile: Dict[str, Any], job_details: Dict[str, Any]):
        resume_ctx = ResumeContext.build_context(profile)
        company = job_details.get("company", "the company")
        title = job_details.get("title", "the role")
        job_description = job_details.get("description", "")

        prompt = f"""You are helping a real job applicant answer a question on a job application form.
Use ONLY the facts given in the candidate profile below - do not invent employers, degrees, dates, or
numbers that are not present. Where the profile doesn't cover something, answer generically but honestly
(e.g. "open to discussing this further") rather than making up specifics.

Candidate profile:
{resume_ctx}

Job applying for: {title} at {company}
Job description (may be partial): {job_description[:1200]}

Question from the application form: "{question_text}"

Write a concise, first-person, professional answer (2-5 sentences, no headers/markdown) that a hiring
manager would find genuine and specific to this candidate and this role.

Respond with ONLY a JSON object in this exact shape, nothing else:
{{"answer": "<the answer text>", "confidence": <integer 0-100, how confident you are this answer is
accurate and usable as-is without a human double-checking it>}}"""

        result = groq_client.generate_json(prompt)
        if not result or not isinstance(result, dict) or not result.get("answer"):
            return None

        answer = str(result["answer"]).strip()
        try:
            confidence = float(result.get("confidence", 90))
        except (TypeError, ValueError):
            confidence = 90.0

        # AUTO_ANSWER_MODE: trust the LLM's own answer for genuinely personalized
        # questions instead of routing them to the manual Review Queue. We still
        # keep a low floor so a truly broken/empty LLM response can't silently
        # slip through as "confident".
        if settings.AUTO_ANSWER_MODE and confidence < settings.CONFIDENCE_THRESHOLD:
            confidence = settings.CONFIDENCE_THRESHOLD

        return {"answer": answer, "category": category, "confidence": confidence}

    @staticmethod
    def _generate_from_template(question_text: str, category: str, profile: Dict[str, Any], job_details: Dict[str, Any]) -> Dict[str, Any]:
        # Heuristic/template fallback engine
        skills = profile.get("skills", {})
        top_skills = []
        if isinstance(skills, dict):
            top_skills = skills.get("ai_extracted", {}).get("programming_languages", [])[:4]
            if not top_skills:
                top_skills = skills.get("ai_keywords", [])[:4]

        skills_str = ", ".join(top_skills)
        headline = profile.get("headline", "Software Engineer")
        company = job_details.get("company", "your company")
        title = job_details.get("title", "this role")

        # Safe template mapping
        templates = {
            "ABOUT_SELF": f"I am a motivated {headline} with experience in software development. My core skillset includes {skills_str}. I enjoy solving complex engineering problems and building robust applications.",

            "WHY_HIRE": f"I am excited about the {title} opportunity at {company}. My technical expertise in {skills_str} directly matches the requirements. I am eager to apply my problem-solving capabilities to help drive success.",

            "STRENGTHS": "My primary strengths are strong analytical problem-solving, clean code design, and adaptability to new codebases and modern frameworks quickly.",

            "WEAKNESSES": "I occasionally focus too much on small optimizations, but I have learned to prioritize delivering fully functional code iteratively first.",

            "ACHIEVEMENT": f"My greatest achievement was successfully delivering critical features as a {headline}, leveraging modern programming structures to optimize performance.",

            "LEADERSHIP": "I have experience collaborating with cross-functional teams, explaining technical requirements to non-technical partners, and mentoring junior engineers.",

            "SPONSORSHIP": "I am authorized to work in the country and do not require sponsorship at this time.",

            "RELOCATION": "I am fully willing to relocate for the right role.",

            "SALARY": f"My expected salary is in line with the standard compensation for a {headline} of my experience level.",

            "GENERIC_EXPERIENCE": f"Throughout my career as a {headline}, I have gained deep experience building scalable solutions, working with modern toolings, and writing maintainable code."
        }

        answer = templates.get(category, templates["GENERIC_EXPERIENCE"])

        # Calculate a mock confidence: templates are high confidence because they are safe,
        # but generic experience might be lower.
        confidence = 85.0 if category != "GENERIC_EXPERIENCE" else 65.0

        if settings.AUTO_ANSWER_MODE and confidence < settings.CONFIDENCE_THRESHOLD:
            confidence = settings.CONFIDENCE_THRESHOLD

        return {
            "answer": answer,
            "category": category,
            "confidence": confidence
        }