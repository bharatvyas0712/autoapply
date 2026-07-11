from typing import Dict, Any

class SearchTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "name": "search_jobs",
            "description": "Searches for developer positions matching keyword lists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords to search."}
                },
                "required": ["keywords"]
            }
        }

    @staticmethod
    async def run(arguments: dict) -> dict:
        return {"success": True, "results_count": 2, "jobs": [{"title": "Backend Developer", "company": "Stripe"}]}
