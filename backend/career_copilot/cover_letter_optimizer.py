class CoverLetterOptimizer:
    """Tailors cover letters to emphasize target job parameters."""
    @staticmethod
    def optimize_letter(original_letter: str, company_name: str, tech_stack: list) -> str:
        tag = f"Specialized in: {', '.join(tech_stack)}."
        return f"{original_letter}\n\n[Optimized for {company_name}]\n{tag}"
