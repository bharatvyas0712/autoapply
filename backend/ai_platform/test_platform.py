import unittest
import asyncio
from tool_registry import ToolRegistry
from tool_validator import ToolValidator
from provider_manager import ProviderManager

class TestAIPlatform(unittest.TestCase):
    def test_tool_registry_discovery(self):
        tools = ToolRegistry.get_all_tools()
        self.assertGreater(len(tools), 0)
        tool_names = [t["name"] for t in tools]
        self.assertIn("analyze_resume", tool_names)
        self.assertIn("search_jobs", tool_names)

    def test_tool_validation(self):
        # Valid parameters
        valid = ToolValidator.validate("analyze_resume", {"resume_path": "test.pdf"})
        self.assertTrue(valid)
        
        # Missing parameters
        invalid = ToolValidator.validate("analyze_resume", {})
        self.assertFalse(invalid)

    def test_provider_switching(self):
        current = ProviderManager.get_active_provider()
        self.assertEqual(current, "groq")

        # Only groq is a valid provider now
        switched = ProviderManager.set_active_provider("groq")
        self.assertTrue(switched)
        self.assertEqual(ProviderManager.get_active_provider(), "groq")

        invalid_switch = ProviderManager.set_active_provider("openai")
        self.assertFalse(invalid_switch)

    def test_mcp_chat_routing(self):
        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(ProviderManager.run_chat(
            messages=[{"role": "user", "content": "search for jobs"}],
            tools=ToolRegistry.get_all_tools()
        ))
        self.assertIn("tool_calls", res)
        self.assertEqual(res["tool_calls"][0]["name"], "search_jobs")

if __name__ == "__main__":
    unittest.main()