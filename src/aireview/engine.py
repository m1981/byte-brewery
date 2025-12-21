# File: src/aireview/engine.py

import json
import re
import logging
from typing import Any
from .domain import Config, CheckDefinition
from .services.runner import CommandRunner
from .services.providers import ProviderFactory
from .errors import CommandError

logger = logging.getLogger("aireview")


class ReviewEngine:
    def __init__(self, config: Config, runner: CommandRunner, provider_factory: ProviderFactory):
        self.config = config
        self.runner = runner
        self.provider_factory = provider_factory

    def build_context(self, check: CheckDefinition) -> str:
        buffer = []
        total_chars = 0

        for ctx_id in check.context_ids:
            definition = self.config.definitions.get(ctx_id)
            if not definition:
                logger.error(f"Context ID '{ctx_id}' not found. Skipping.")
                continue

            try:
                output = self.runner.run(definition.cmd)
            except CommandError as e:
                raise e

            if not output or not output.strip():
                # Refactor: Removed brittle string matching for hints.
                # Keep it simple: if empty, just warn.
                print(f"  ⚠️  Context '{ctx_id}' returned empty output.")
                continue

            remaining_chars = check.max_chars - total_chars
            if len(output) > remaining_chars:
                logger.warning(f"Truncating output for context '{ctx_id}' (Limit: {check.max_chars})")
                output = output[:remaining_chars] + "\n... [TRUNCATED]"

            total_chars += len(output)
            buffer.append(f"### Context: {definition.tag}\n```text\n{output}\n```\n")

            if total_chars >= check.max_chars:
                break

        return "\n".join(buffer)

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parses AI response. Defaults to FAIL if parsing fails (Fail-Safe)."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON block in markdown
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass

            # Refactor: If we can't parse it, we can't trust it. Fail safe.
            return {
                "status": "FAIL",
                "reason": f"Could not parse AI response as JSON. Raw response start: {response[:50]}..."
            }

    def _print_debug_info(self, metadata: dict[str, Any], full_message: str):
        meta_str = " | ".join(f"{k}: {v}" for k, v in metadata.items())
        print(f"\033[90m[DEBUG] {meta_str}\033[0m")
        print("")
        for line in full_message.splitlines():
            print(f"  \033[90m│\033[0m {line}")
        print("")

    def run_check(self, check_id: str) -> bool:
        check = next((c for c in self.config.checks if c.id == check_id), None)
        if not check: return False

        print("=" * 80)
        print(f"CHECK: {check_id}")
        print("=" * 80)

        prompt_def = self.config.prompts.get(check.prompt_id)

        try:
            context = self.build_context(check)
        except CommandError as e:
            print(f"  ❌ Error gathering context: {e}")
            return False

        if not context.strip():
            print("\n  ⏭️  Skipped Check (No context available)\n")
            return True

        full_message = f"{prompt_def.text}\n\n{context}"

        # Refactor: Get provider from factory on demand
        provider = self.provider_factory.get_provider(check.model)

        if logger.isEnabledFor(logging.DEBUG):
            metadata = provider.get_metadata(check.model)
            self._print_debug_info(metadata, full_message)

        raw_response = provider.analyze(check.model, full_message)

        result = self._parse_json_response(raw_response)
        status = result.get("status", "FAIL").upper()
        reason = result.get("reason", "No reason provided")

        if logger.isEnabledFor(logging.DEBUG):
            print("-" * 80)

        symbol = "✔" if status == "PASS" else "✘"
        print(f"{symbol} {status} | Reason: {reason}\n")

        return status == "PASS"