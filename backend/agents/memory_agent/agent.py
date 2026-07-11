from memory_store import MemoryStore
from episodic_memory import EpisodicMemory
from semantic_memory import SemanticMemory
from company_memory import CompanyMemory
from application_memory import ApplicationMemory
from feedback_memory import FeedbackMemory
from answer_memory import AnswerMemory
from resume_memory import ResumeMemory
from learning_engine import LearningEngine
from typing import Dict, Any, List

class MemoryAgent:
    """
    Core wrapper coordinating memory accesses and queries.
    Allows easy interface for LangGraph orchestrator.
    """
    
    @staticmethod
    async def recall_relevant_context(user_id: int, query: str) -> Dict[str, Any]:
        """Runs vector search to load prior similar approved answers and facts."""
        memories = await MemoryStore.search_memory(user_id, query, top_k=3)
        return {
            "query": query,
            "relevant_memories": memories
        }
