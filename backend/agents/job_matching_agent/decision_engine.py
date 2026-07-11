from config import settings

def get_decision(overall_score: float) -> str:
    if overall_score >= settings.THRESHOLD_AUTO_APPLY:
        return "AUTO_APPLY"
    elif overall_score >= settings.THRESHOLD_REVIEW:
        return "REVIEW_REQUIRED"
    else:
        return "SKIP"
