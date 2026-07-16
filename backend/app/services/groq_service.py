import json
from typing import Optional, Dict, Any
from groq import Groq
from app.config import settings

class GroqService:
    def __init__(self):
        # We will initialize on first call to support empty key on startup, or just initialize directly
        self._client: Optional[Groq] = None

    @property
    def client(self) -> Groq:
        if self._client is None:
            if not settings.GROQ_API_KEY:
                # Fallback to GROQ_API_KEY environment variable directly if setting is empty
                import os
                api_key = os.getenv("GROQ_API_KEY", "")
                if not api_key:
                    raise ValueError("GROQ_API_KEY is not set in configuration or environment variables.")
                self._client = Groq(api_key=api_key)
            else:
                self._client = Groq(api_key=settings.GROQ_API_KEY)
        return self._client

    def chat_completion(
        self,
        prompt: str,
        system_instruction: str = "You are a helpful AI career assistant.",
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.2,
        response_format: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None
    ) -> str:
        try:
            # Use per-user key if provided, otherwise fall back to global client
            if api_key:
                active_client = Groq(api_key=api_key)
            else:
                active_client = self.client

            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
            
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            if response_format:
                kwargs["response_format"] = response_format

            chat_completion = active_client.chat.completions.create(**kwargs)
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Error in Groq API request: {e}")
            raise

groq_service = GroqService()
