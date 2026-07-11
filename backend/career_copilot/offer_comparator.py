from typing import List, Dict, Any

class OfferComparator:
    """
    Rates and compares multiple offer letters side-by-side.
    """
    
    @staticmethod
    def compare_offers(offers: List[Dict[str, Any]]) -> Dict[str, Any]:
        scored = []
        for o in offers:
            salary = o.get("salary", 0.0)
            benefits = o.get("benefits_rating", 5) # scale 1-10
            growth = o.get("growth_rating", 5)
            
            # Simple formula
            score = (salary / 1000) + (benefits * 2) + (growth * 2)
            scored.append({
                "company": o.get("company"),
                "role": o.get("role"),
                "overall_score": round(score, 1)
            })
            
        scored.sort(key=lambda x: x["overall_score"], reverse=True)
        return {"comparison": scored}
