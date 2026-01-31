from fastapi import APIRouter, Request
import asyncio
from pydantic import BaseModel
import requests

from core.config import settings

router = APIRouter()

class ChatRequest(BaseModel):
    prompt: str
    user_id: str = "founder"

@router.post("/api/ai/chat")
async def ai_chat(request: ChatRequest):
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": request.prompt,
        "stream": False
    }
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(f"{settings.OLLAMA_URL}/api/generate", json=payload, timeout=30))
        response.raise_for_status()
        data = response.json()
        return {"response": data.get("response", "No response from Ollama.")}
    except Exception as e:
        return {"error": str(e)}
