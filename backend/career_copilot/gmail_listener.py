from typing import List, Dict, Any

class GmailListener:
    """
    Parses inbox logs to detect interview invitations, assessments or offers.
    """
    
    @staticmethod
    def scan_inbox() -> List[Dict[str, Any]]:
        # Mock scanned emails return payload
        return [
            {"id": "msg_123", "sender": "jane@stripe.com", "subject": "Stripe Interview Schedule Invitation", "type": "interview_invite"},
            {"id": "msg_124", "sender": "noreply@vercel.com", "subject": "Vercel Hackerrank Assessment Link", "type": "assessment_link"}
        ]
