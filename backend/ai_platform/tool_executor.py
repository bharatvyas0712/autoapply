from tool_registry import ToolRegistry
from repository import AsyncSessionLocal, ToolCall, AuditLog
from typing import Dict, Any

class ToolExecutor:
    """
    Executes selected tools safely and logs traces to the database.
    """
    
    @staticmethod
    async def execute(name: str, arguments: dict, conversation_id: int = 1) -> dict:
        tool = ToolRegistry.get_tool(name)
        if not tool:
            return {"success": False, "error": f"Tool '{name}' not found."}
            
        try:
            result = await tool.run(arguments)
            
            # Log Tool Call trace
            async with AsyncSessionLocal() as db:
                tc = ToolCall(
                    conversation_id=conversation_id,
                    tool_name=name,
                    input_parameters=arguments,
                    output_result=result,
                    execution_status="success"
                )
                db.add(tc)
                
                # Log to AuditLog
                audit = AuditLog(
                    user_id=1,
                    action=f"EXECUTE_TOOL:{name}",
                    details={"arguments": arguments, "result": result}
                )
                db.add(audit)
                await db.commit()
                
            return result
        except Exception as e:
            async with AsyncSessionLocal() as db:
                tc = ToolCall(
                    conversation_id=conversation_id,
                    tool_name=name,
                    input_parameters=arguments,
                    execution_status="failed"
                )
                db.add(tc)
                await db.commit()
            return {"success": False, "error": str(e)}
