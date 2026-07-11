from typing import Dict, Any

class EmailTool:
    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "name": "send_email",
            "description": "Sends follow-up notifications or emails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Target email address."},
                    "subject": {"type": "string", "description": "Subject line."},
                    "body": {"type": "string", "description": "Email content."}
                },
                "required": ["to", "subject", "body"]
            }
        }

    @staticmethod
    async def run(arguments: dict) -> dict:
        return {"success": True, "message": "Email sent successfully."}
