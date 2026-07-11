from typing import Dict, Any

class NetworkingAssistant:
    """
    Drafts connection messages, referral requests, and recruiter outreach blocks.
    """
    
    @staticmethod
    def generate_message(contact_name: str, company: str, msg_type: str = "connection_request") -> str:
        if msg_type == "referral":
            return (
                f"Hi {contact_name},\n\n"
                f"I noticed the Backend Engineer role open at {company} and would love to ask "
                "about your experience there. Would you be open to sharing a quick referral? "
                "Thank you!"
            )
        # Default connection request
        return f"Hi {contact_name}, I see you work in engineering at {company}. I am also a developer and would love to connect!"
