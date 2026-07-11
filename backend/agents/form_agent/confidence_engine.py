from config import settings

class ConfidenceEngine:
    """
    Evaluates whether generated answers are confident enough to submit without review.
    """
    
    @staticmethod
    def check_confidence(confidence_score: float) -> bool:
        """Returns True if the score meets the minimum threshold, False otherwise."""
        return confidence_score >= settings.CONFIDENCE_THRESHOLD
