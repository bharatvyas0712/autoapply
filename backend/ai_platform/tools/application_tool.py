from typing import Dict, Any

class ApplicationTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "name": "submit_application",
            "description": "Fills form and submits application target.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "integer", "description": "Job ID to submit."}
                },
                "required": ["job_id"]
            }
        }

    @staticmethod
    async def run(arguments: dict) -> dict:
        return {"success": True, "status": "submitted"}
