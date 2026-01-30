from fastapi import APIRouter, Request
import asyncio
from pydantic import BaseModel
import requests
import os

router = APIRouter()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

class ChatRequest(BaseModel):
    prompt: str
    user_id: str = "founder"

@router.post("/api/ai/chat")
async def ai_chat(request: ChatRequest):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": request.prompt,
        "stream": False
    }
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=30))
        response.raise_for_status()
        data = response.json()
        return {"response": data.get("response", "No response from Ollama.")}
    except Exception as e:
        return {"error": str(e)}
