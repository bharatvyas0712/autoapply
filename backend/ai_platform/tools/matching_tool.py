from typing import Dict, Any

class MatchingTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "name": "calculate_match",
            "description": "Evaluates matching scores between candidates and jobs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "integer", "description": "Target job ID."}
                },
                "required": ["job_id"]
            }
        }

    @staticmethod
    async def run(arguments: dict) -> dict:
        return {"success": True, "score": 85.0}
