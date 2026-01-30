"""
Ollama Client for local LLM inference.
Provides AI text generation using locally hosted Ollama models.
"""

import httpx
from typing import Dict, Any, List, Optional
from utils.logger import logger


class OllamaClient:
    """Client for Ollama local LLM server."""
    
    def __init__(self, base_url: Optional[str] = None):
        if base_url is None:
            try:
                from core.config import settings
                base_url = getattr(settings, "OLLAMA_SERVER_URL", None) or "http://localhost:11434"
            except Exception:
                base_url = "http://localhost:11434"
        self.base_url = base_url.rstrip("/")
        self.timeout = 120.0
    
    async def generate(
        self,
        prompt: str,
        model: str = "llama2",
        system: str = None,
        context: List[int] = None,
        options: Dict[str, Any] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Generate text completion from Ollama."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
        }
        
        if system:
            payload["system"] = system
        if context:
            payload["context"] = context
        if options:
            payload["options"] = options
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Ollama generate error: {e}")
            return {"error": str(e), "response": ""}
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama2",
        options: Dict[str, Any] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Chat completion from Ollama."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        
        if options:
            payload["options"] = options
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Ollama chat error: {e}")
            return {"error": str(e), "message": {"role": "assistant", "content": ""}}
    
    async def embeddings(
        self,
        prompt: str,
        model: str = "llama2",
    ) -> Dict[str, Any]:
        """Get embeddings from Ollama."""
        payload = {
            "model": model,
            "prompt": prompt,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Ollama embeddings error: {e}")
            return {"error": str(e), "embedding": []}
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Ollama list_models error: {e}")
            return {"error": str(e), "models": []}

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "llama3.2",
    ) -> str:
        """Generate text and return the response string (for billing chat, explain, etc.)."""
        result = await self.generate(
            prompt=prompt,
            model=model,
            system=system_prompt,
        )
        if isinstance(result, dict) and "response" in result:
            return (result.get("response") or "").strip()
        return ""
