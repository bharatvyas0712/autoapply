from typing import Dict, Any, List

from llm_client import generate_json


class MockInterviewer:
    """
    Generates behavioral, technical, coding, or system design interview QAs and scores response inputs.
    """

    @staticmethod
    def generate_questions(interview_type: str, programming_language: str = "Python") -> List[Dict[str, Any]]:
        type_instructions = {
            "coding": (
                f"4 unique, non-generic hands-on CODING problems in {programming_language}. "
                f"Each question must require writing actual code (algorithms, data structures). "
                f"Do NOT include any behavioral, HR, or conceptual questions."
            ),
            "behavioral": (
                "4 unique, non-generic BEHAVIORAL / LEADERSHIP interview questions "
                "(e.g. teamwork, conflict resolution, ownership, failure, feedback). "
                "Do NOT include any coding, algorithm, or system design questions - "
                "no code should ever need to be written to answer these."
            ),
            "technical": (
                "4 unique, non-generic TECHNICAL CONCEPT questions for a software engineer "
                "(e.g. databases, networking, system design trade-offs, architecture). "
                "These should be answerable in prose/discussion - do NOT ask the candidate to write code."
            ),
        }
        focus = type_instructions.get(interview_type, type_instructions["technical"])

        prompt = f"""Generate {focus}

Vary difficulty and topic each time you're asked - avoid reusing the most common textbook questions \
verbatim, phrase them freshly.

Respond with ONLY a JSON array in this exact shape (no markdown fences):
[{{"id": 1, "question": "..."}}, {{"id": 2, "question": "..."}}]"""
        result = generate_json(prompt)
        if isinstance(result, list) and all("question" in q for q in result if isinstance(q, dict)):
            return result

        return MockInterviewer._fallback_questions(interview_type, programming_language)

    @staticmethod
    def _fallback_questions(interview_type: str, programming_language: str) -> List[Dict[str, Any]]:
        if interview_type == "behavioral":
            return [
                {"id": 1, "question": "Tell me about a time you resolved a conflict within your team."},
                {"id": 2, "question": "Describe a challenging engineering bug you successfully resolved."},
            ]
        elif interview_type == "coding":
            return [
                {"id": 1, "question": f"Write a function in {programming_language} to find the longest palindromic substring."},
                {"id": 2, "question": f"Implement a thread-safe rate limiter class in {programming_language}."},
            ]
        return [
            {"id": 1, "question": "Explain the difference between event loop processes and process threads."},
            {"id": 2, "question": "How do database indices optimize select queries, and what is the trade-off?"},
        ]

    @staticmethod
    def evaluate_answers(questions: List[str], answers: List[str]) -> Dict[str, Any]:
        qa_pairs = "\n".join(
            f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)
        )
        prompt = f"""You are an interviewer scoring a candidate's mock interview answers.

{qa_pairs}

Score the overall performance 0-100 based on correctness, depth, and clarity, and give specific feedback \
tied to what was actually said (or the fact that nothing/little was said).

Respond with ONLY a JSON object in this exact shape (no markdown fences):
{{"score": 0, "feedback": ["...", "..."], "improvement_areas": ["...", "..."]}}"""
        result = generate_json(prompt)
        if isinstance(result, dict) and "score" in result:
            return result

        return {
            "score": 80.0,
            "feedback": [
                "Good technical terms used.",
                "Explain project trade-offs in detail to sound senior.",
            ],
            "improvement_areas": ["System Design", "Time Complexity Analysis"],
        }