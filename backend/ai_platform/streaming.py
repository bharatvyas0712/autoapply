import json
import asyncio
from typing import AsyncGenerator

class SSEStreamManager:
    """
    Formulates SSE streaming chunks to enable live typing animation in the UI.
    """
    
    @staticmethod
    async def generate_chunks(response_text: str) -> AsyncGenerator[str, None]:
        # Emulate active streaming chunks
        words = response_text.split(" ")
        for word in words:
            yield f"data: {json.dumps({'delta': word + ' '})}\n\n"
            await asyncio.sleep(0.08)
        yield "data: [DONE]\n\n"
