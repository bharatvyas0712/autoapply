import os
from typing import Dict, Any

import groq_client


class ResumeTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "name": "analyze_resume",
            "description": "Extracts skills, details, and context facts from resume files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resume_path": {"type": "string", "description": "Absolute path to the resume PDF."}
                },
                "required": ["resume_path"]
            }
        }

    @staticmethod
    def _extract_text(resume_path: str) -> str:
        ext = os.path.splitext(resume_path)[1].lower()
        if ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(resume_path)
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        elif ext == ".docx":
            import docx2txt
            return docx2txt.process(resume_path) or ""
        else:
            with open(resume_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

    @staticmethod
    async def run(arguments: dict) -> dict:
        resume_path = arguments.get("resume_path", "")

        if not resume_path or not os.path.isfile(resume_path):
            return {
                "success": False,
                "error": f"Resume file not found at '{resume_path}'.",
            }

        try:
            text = ResumeTool._extract_text(resume_path)
        except Exception as e:
            return {"success": False, "error": f"Failed to read resume file: {e}"}

        if not text.strip():
            return {"success": False, "error": "Resume file appears to be empty or unreadable."}

        prompt = f"""Extract structured information from this resume text.

Resume:
{text[:6000]}

Respond with ONLY a JSON object in this exact shape (no markdown fences):
{{"skills": ["...", "..."], "summary": "one-line professional summary", "keywords": ["...", "..."]}}"""

        result = groq_client.generate_json(prompt)
        if isinstance(result, dict) and "skills" in result:
            return {"success": True, **result}

        return {
            "success": False,
            "error": "Could not extract structured data from the resume (LLM unavailable or parsing failed).",
        }