from typing import Dict, Any

class MemoryTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "name": "search_memory",
            "description": "Searches stored facts and historical outcomes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Text query."}
                },
                "required": ["query"]
            }
        }

    @staticmethod
    async def run(arguments: dict) -> dict:
        return {"success": True, "results": ["Previous answer matching FastAPI"]}
