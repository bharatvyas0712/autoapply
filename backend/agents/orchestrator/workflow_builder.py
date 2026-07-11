from graph import build_orchestrator_graph
from langgraph.graph import END

class WorkflowBuilder:
    """
    Compiles and exports graph visualization structures (Mermaid charts, PNG visualizers).
    """
    
    @staticmethod
    def generate_mermaid() -> str:
        compiled = build_orchestrator_graph()
        try:
            # LangGraph compiled graphs have a get_graph() method which returns a printable structure
            return compiled.get_graph().draw_mermaid()
        except Exception:
            # Fallback printable Mermaid format mapping
            return (
                "graph TD\n"
                "  Start --> resume_intelligence\n"
                "  resume_intelligence --> job_search\n"
                "  job_search --> job_matching\n"
                "  job_matching --> select_next_job\n"
                "  select_next_job -->|Score >= 70| browser_automation\n"
                "  select_next_job -->|Score < 70| select_next_job\n"
                "  browser_automation --> select_next_job\n"
                "  select_next_job -->|No Jobs| End"
            )
            
    @staticmethod
    def generate_png() -> bytes:
        compiled = build_orchestrator_graph()
        try:
            return compiled.get_graph().draw_mermaid_png()
        except Exception:
            # Return empty bytes if rendering libraries (pygraphviz, etc) missing
            return b""
