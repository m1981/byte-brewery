# File: src/aireview/services/providers.py

import os
import json
from typing import Protocol, Any, Dict


class AIProvider(Protocol):
    def analyze(self, model: str, full_message: str) -> str: ...
    def get_metadata(self, model: str) -> dict[str, Any]: ...


class OpenAIProvider:
    def __init__(self):
        self.client = None
        if os.environ.get("OPENAI_API_KEY"):
            try:
                import openai
                self.client = openai.OpenAI()
            except ImportError:
                pass

    def get_metadata(self, model: str) -> dict[str, Any]:
        is_json_mode = "gpt-4" in model or "gpt-3.5-turbo-1106" in model
        return {
            "provider": "OpenAI",
            "model": model,
            "temperature": 1.0,
            "response_format": "json_object" if is_json_mode else "text"
        }

    def analyze(self, model: str, full_message: str) -> str:
        if not self.client:
            return '{"status": "FAIL", "reason": "OpenAI client not ready (Check OPENAI_API_KEY)"}'
        try:
            meta = self.get_metadata(model)
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": full_message}],
                "temperature": meta["temperature"]
            }
            if meta["response_format"] == "json_object":
                kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            return json.dumps({"status": "FAIL", "reason": f"API Error: {str(e)}"})


class AnthropicProvider:
    def __init__(self):
        self.client = None
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                import anthropic
                self.client = anthropic.Anthropic()
            except ImportError:
                pass

    def get_metadata(self, model: str) -> Dict[str, Any]:
        return {
            "provider": "Anthropic",
            "model": model,
            "temperature": 1.0,
            "max_tokens": 4096,
            "response_format": "text"
        }

    def analyze(self, model: str, full_message: str) -> str:
        if not self.client: return '{"status": "FAIL", "reason": "Anthropic client not ready (Check ANTHROPIC_API_KEY)"}'
        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": full_message}]
            )
            return message.content[0].text
        except Exception as e:
            return json.dumps({"status": "FAIL", "reason": f"Anthropic API Error: {str(e)}"})


class GeminiProvider:
    def __init__(self):
        self.genai = None
        if os.environ.get("GOOGLE_API_KEY"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
                self.genai = genai
            except ImportError:
                pass

    def get_metadata(self, model: str) -> Dict[str, Any]:
        return {
            "provider": "Google Gemini",
            "model": model,
            "temperature": 1.0,
            "max_tokens": "Model Default",
            "response_format": "json_mode"
        }

    def analyze(self, model: str, full_message: str) -> str:
        if not self.genai: return '{"status": "FAIL", "reason": "Google GenAI client not ready (Check GOOGLE_API_KEY)"}'
        try:
            model_instance = self.genai.GenerativeModel(model)
            response = model_instance.generate_content(full_message)
            return response.text
        except Exception as e:
            return json.dumps({"status": "FAIL", "reason": f"Gemini API Error: {str(e)}"})


class MockAIProvider:
    def get_metadata(self, model: str) -> dict[str, Any]:
        return {
            "provider": "Mock (Dry Run)",
            "model": model,
            "temperature": 0.0,
            "response_format": "json_object"
        }

    def analyze(self, model: str, full_message: str) -> str:
        return '{"status": "PASS", "reason": "Dry Run Successful"}'


class ProviderFactory:
    def __init__(self, is_dry_run: bool = False):
        self.is_dry_run = is_dry_run
        # Simple cache
        self._instances: Dict[str, AIProvider] = {}

    def get_provider(self, model: str) -> AIProvider:
        if self.is_dry_run:
            return MockAIProvider()

        # 1. Handle Anthropic
        if model.startswith("claude"):
            if "anthropic" not in self._instances:
                self._instances["anthropic"] = AnthropicProvider()
            return self._instances["anthropic"]

        # 2. Handle Google (Was Dead Code)
        if model.startswith("gemini"):
            if "gemini" not in self._instances:
                self._instances["gemini"] = GeminiProvider()
            return self._instances["gemini"]

        # 3. Default to OpenAI
        if "openai" not in self._instances:
            self._instances["openai"] = OpenAIProvider()
        return self._instances["openai"]