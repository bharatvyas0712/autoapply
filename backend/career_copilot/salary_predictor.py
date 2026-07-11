from typing import Dict, Any

from llm_client import generate_json


class SalaryPredictor:
    """
    Estimates compensation ranges based on role, location, and experience.
    """

    @staticmethod
    def predict(role: str, location: str, experience_years: int = 0) -> Dict[str, Any]:
        prompt = f"""You are a compensation analyst. Estimate a realistic salary range for this role, \
using current market data for the specified location and experience level.

Role: {role}
Location: {location}
Experience: {experience_years} years

Use the correct local currency for the location (e.g. INR for Indian cities, USD for US cities, \
GBP for UK, etc). Base the range on real market rates for that specific city/country and role \
seniority - do not default to US-centric numbers for non-US locations.

Respond with ONLY a JSON object in this exact shape (no markdown fences):
{{"predicted_min": 0, "predicted_max": 0, "currency": "USD", "currency_symbol": "$", "notes": "..."}}
Amounts should be annual, in whole units of the currency (e.g. INR annual CTC, not per month)."""

        result = generate_json(prompt)
        if isinstance(result, dict) and all(
            k in result for k in ("predicted_min", "predicted_max", "currency")
        ):
            return result

        return SalaryPredictor._fallback_predict(role, location, experience_years)

    @staticmethod
    def _fallback_predict(role: str, location: str, experience_years: int) -> Dict[str, Any]:
        """Deterministic backup used only if the LLM is unavailable or fails."""
        indian_cities = ("bangalore", "bengaluru", "hyderabad", "pune", "mumbai",
                          "delhi", "chennai", "gurgaon", "gurugram", "noida", "india")
        is_india = any(city in location.lower() for city in indian_cities)

        multiplier = 1.0
        if "senior" in role.lower() or experience_years > 5:
            multiplier = 1.5
        elif "lead" in role.lower():
            multiplier = 1.8

        if is_india:
            base = 700000.0  # INR annual CTC, fresher baseline
            currency, symbol = "INR", "\u20b9"
        else:
            base = 80000.0
            currency, symbol = "USD", "$"
            if "remote" in location.lower() or "sf" in location.lower() or "ny" in location.lower():
                base = 110000.0

        pred_min = base * multiplier
        pred_max = pred_min * 1.35

        return {
            "predicted_min": round(pred_min, 2),
            "predicted_max": round(pred_max, 2),
            "currency": currency,
            "currency_symbol": symbol,
            "notes": "Estimate from static fallback model (AI estimate unavailable).",
        }