from typing import Dict, Any, List
from tools.resume_tool import ResumeTool
from tools.search_tool import SearchTool
from tools.matching_tool import MatchingTool
from tools.browser_tool import BrowserTool
from tools.application_tool import ApplicationTool
from tools.memory_tool import MemoryTool
from tools.analytics_tool import AnalyticsTool
from tools.email_tool import EmailTool
from tools.scheduler_tool import SchedulerTool

class ToolRegistry:
    """
    Maintains active tool registration maps and exports schemas for LLM contexts.
    """
    _tools = {
        "analyze_resume": ResumeTool,
        "search_jobs": SearchTool,
        "calculate_match": MatchingTool,
        "open_browser": BrowserTool,
        "submit_application": ApplicationTool,
        "search_memory": MemoryTool,
        "get_analytics": AnalyticsTool,
        "send_email": EmailTool,
        "schedule_application": SchedulerTool
    }

    @staticmethod
    def get_all_tools() -> List[Dict[str, Any]]:
        return [tool.get_definition() for tool in ToolRegistry._tools.values()]

    @staticmethod
    def get_tool(name: str) -> Any:
        return ToolRegistry._tools.get(name)
