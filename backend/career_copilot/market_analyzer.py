from typing import Dict, Any, List

class MarketAnalyzer:
    """
    Extracts high-demand frameworks and top hiring companies.
    """
    
    @staticmethod
    def get_market_trends() -> Dict[str, Any]:
        return {
            "trending_frameworks": ["FastAPI", "LangChain", "Next.js", "TailwindCSS"],
            "top_hiring_companies": ["Stripe", "Vercel", "Supabase", "OpenAI"],
            "emerging_roles": ["AI Integrations Engineer", "Fullstack Agent Developer"]
        }
