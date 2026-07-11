class EmailGenerator:
    """
    Generates tailored application emails, follow-up traces, and thank you notes.
    """
    
    @staticmethod
    def generate_email(company_name: str, recipient: str, template_type: str = "follow_up") -> str:
        if template_type == "thank_you":
            return (
                f"Dear {recipient},\n\n"
                f"Thank you for taking the time to speak with me today about the role at {company_name}. "
                "I really enjoyed our conversation and look forward to next steps."
            )
        # Default follow up
        return (
            f"Dear {recipient},\n\n"
            f"I am following up on my application for the software engineering position at {company_name}. "
            "I wanted to reiterate my strong interest and see if there are any updates."
        )
