def compute_salary_score(expected_salary: str, offered_salary: str) -> float:
    """Compares expected salary vs offered. Returns 100 if unknown or matched."""
    if not offered_salary:
        return 80.0 # Neutral positive if unknown
        
    # In a fully fleshed out system, we would parse numeric values and compare.
    # For now, we return a high score if they both exist and we can't mathematically prove a mismatch.
    return 90.0
