# File: src/aireview/services/providers.py

import os
import json
import logging
from typing import Protocol, Any, Dict, Type
from ..domain import ReviewResult

logger = logging.getLogger("aireview")

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
                logger.warning("OpenAI library not installed.")

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
                logger.warning("Anthropic library not installed.")

    def get_metadata(self, model: str) -> Dict[str, Any]:
        return {
            "provider": "Anthropic",
            "model": model,
            "temperature": 1.0,
            "max_tokens": 4096,
            "response_format": "structured_output"
        }

    def analyze(self, model: str, full_message: str) -> str:
        if not self.client:
            return '{"status": "FAIL", "reason": "Anthropic client not ready"}'

        try:
            # USE THE NEW BETA PARSE METHOD
            response = self.client.beta.messages.parse(
                model=model,
                max_tokens=4096,
                betas=["structured-outputs-2025-11-13"], # Enable Beta
                messages=[{"role": "user", "content": full_message}],
                output_format=ReviewResult # Pass the Pydantic Model
            )

            # The SDK returns a parsed object. We convert it back to JSON string
            # so the Engine can handle it uniformly (or we could refactor Engine to take objects)
            # For minimal refactoring, we return JSON string.
            return response.parsed_output.model_dump_json()

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
                logger.warning("Google GenAI library not installed.")

    def get_metadata(self, model: str) -> Dict[str, Any]:
        return {
            "provider": "Google Gemini",
            "model": model,
            "temperature": 1.0,
            "max_tokens": "Model Default",
            "response_format": "json_mode"
        }

    def analyze(self, model: str, full_message: str) -> str:
        if not self.genai:
            return '{"status": "FAIL", "reason": "Google GenAI client not ready (Check GOOGLE_API_KEY)"}'
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
    """
    Factory using a Registry Pattern to adhere to OCP.
    New providers can be registered without modifying the get_provider logic.
    """

    _registry: Dict[str, Type[AIProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
        "mock": MockAIProvider
    }

    def __init__(self, is_dry_run: bool = False):
        self.is_dry_run = is_dry_run
        # Simple cache
        self._instances: Dict[str, AIProvider] = {}

    def get_provider(self, model: str) -> AIProvider:
        if self.is_dry_run:
            return self._get_instance("mock")

        # OCP: Logic relies on mapping, not hardcoded strings
        key = self._resolve_provider_key(model)
        return self._get_instance(key)

    def _resolve_provider_key(self, model: str) -> str:
        """Map model names to provider keys."""
        if model.startswith("claude"): return "anthropic"
        if model.startswith("gemini"): return "gemini"
        return "openai" # Default

    def _get_instance(self, key: str) -> AIProvider:
        if key not in self._instances:
            provider_cls = self._registry.get(key, OpenAIProvider)
            self._instances[key] = provider_cls()
        return self._instances[key]