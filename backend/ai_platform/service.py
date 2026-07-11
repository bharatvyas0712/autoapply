import json
from llm_router import LLMRouter
from tool_registry import ToolRegistry
from tool_executor import ToolExecutor
from provider_manager import ProviderManager
from conversation_manager import ConversationManager
from context_builder import ContextBuilder
from repository import AsyncSessionLocal, LLMProvider
from sqlalchemy.future import select
from typing import Dict, Any, List

class AIPlatformService:
    @staticmethod
    async def chat(conversation_id: int, message: str) -> Dict[str, Any]:
        # 1. Get history
        conv = await ConversationManager.get_or_create(conversation_id)
        messages = list(conv.messages)
        messages.append({"role": "user", "content": message})

        # 2. Prepend system context so the model knows its role/tools instead
        # of receiving a bare, context-free conversation.
        if not messages or messages[0].get("role") != "system":
            system_prompt = ContextBuilder.build_system_context({"name": "the current user"})
            messages = [{"role": "system", "content": system_prompt}] + messages

        # Save user message
        await ConversationManager.add_message(conversation_id, "user", message)
        
        # 3. Match tools
        tools = ToolRegistry.get_all_tools()
        
        # 4. Route to active LLM
        response = await LLMRouter.route_chat(messages, tools)

        tool_calls = response.get("tool_calls")
        executed = []

        if tool_calls:
            # Build the assistant turn that requested the tool call(s), in
            # proper OpenAI/Groq shape (with real ids), so we can follow up
            # with the tool results and get a real answer back.
            assistant_turn = {
                "role": "assistant",
                "content": response.get("content") or "",
                "tool_calls": [
                    {
                        "id": tc.get("id") or f"call_{i}",
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]),
                        },
                    }
                    for i, tc in enumerate(tool_calls)
                ],
            }
            follow_up_messages = messages + [assistant_turn]

            for i, tc in enumerate(tool_calls):
                result = await ToolExecutor.execute(tc["name"], tc["arguments"], conversation_id)
                executed.append({"name": tc["name"], "arguments": tc["arguments"], "result": result})
                follow_up_messages.append({
                    "role": "tool",
                    "tool_call_id": assistant_turn["tool_calls"][i]["id"],
                    "content": json.dumps(result),
                })

            # 5. Give the model the tool results so it can produce a real,
            # natural-language answer instead of leaving the raw JSON as the reply.
            final = await LLMRouter.route_chat(follow_up_messages, tools=[])
            final_content = final.get("content", "") or "Done."
        else:
            final_content = response.get("content", "")

        # Save assistant message (simplified shape for storage/display)
        await ConversationManager.add_message(
            conversation_id,
            "assistant",
            final_content,
            [{"name": t["name"], "arguments": t["arguments"]} for t in executed] or None,
        )

        return {
            "role": "assistant",
            "content": final_content,
            "tool_calls": [{"name": t["name"], "arguments": t["arguments"]} for t in executed] or None,
            "tool_results": [t["result"] for t in executed] or None,
        }

    @staticmethod
    async def run_tool(name: str, arguments: dict, conversation_id: int) -> dict:
        return await ToolExecutor.execute(name, arguments, conversation_id)

    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        return ToolRegistry.get_all_tools()

    @staticmethod
    async def get_providers(user_id: int) -> List[LLMProvider]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(LLMProvider))
            providers = result.scalars().all()
            if not providers:
                # Seed defaults
                p_list = [
                    LLMProvider(provider_name="groq", model_name="llama-3.3-70b-versatile", is_active=True),
                ]
                db.add_all(p_list)
                await db.commit()
                return p_list
            return providers

    @staticmethod
    async def switch_provider(provider_name: str) -> bool:
        success = ProviderManager.set_active_provider(provider_name)
        if success:
            async with AsyncSessionLocal() as db:
                # Reset active flags
                await db.execute(select(LLMProvider))  # Just updates records in loop
                res = await db.execute(select(LLMProvider))
                for p in res.scalars().all():
                    p.is_active = (p.provider_name == provider_name.lower())
                await db.commit()
            return True
        return False
        
    @staticmethod
    async def get_conversations(user_id: int) -> List[Any]:
        return await ConversationManager.get_history(user_id)