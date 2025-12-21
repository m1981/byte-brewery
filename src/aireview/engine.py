# File: src/aireview/engine.py

import json
import re
import logging
from typing import Any
from .domain import Config, CheckDefinition
from .services.runner import CommandRunner
from .services.providers import ProviderFactory
from .services.debugger import Debugger
from .errors import CommandError

logger = logging.getLogger("aireview")


class ReviewEngine:
    # FIX: Added 'debugger: Debugger' to the signature
    def __init__(self, config: Config, runner: CommandRunner, provider_factory: ProviderFactory, debugger: Debugger):
        self.config = config
        self.runner = runner
        self.provider_factory = provider_factory
        self.debugger = debugger

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
                print(f"  ⚠️  Context '{ctx_id}' returned empty output.")
                continue

            # --- SAFETY CHECK START ---
            output_len = len(output)

            # Check if adding this specific output would breach the limit
            if total_chars + output_len > check.max_chars:
                raise CommandError(
                    f"SAFETY LIMIT EXCEEDED: Context '{ctx_id}' generated {output_len} chars. "
                    f"Total would be {total_chars + output_len}, but limit is {check.max_chars}. "
                    "Review cannot proceed safely without full context."
                )
            # --- SAFETY CHECK END ---

            total_chars += output_len
            buffer.append(f"### Context: {definition.tag}\n```text\n{output}\n```\n")

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

    def run_check(self, check_id: str, override_context: str = None) -> bool:
        check = next((c for c in self.config.checks if c.id == check_id), None)
        if not check: return False

        print("=" * 80)
        print(f"CHECK: {check_id}")
        print("=" * 80)

        prompt_def = self.config.prompts.get(check.prompt_id)

        # 1. Handle Context (Req 2: Manual Override)
        if override_context:
            # Safety check for manual overrides too!
            if len(override_context) > check.max_chars:
                 print(f"  ❌ SAFETY ERROR: Manual context file is too large ({len(override_context)} > {check.max_chars})")
                 return False
            context = override_context
        else:
            try:
                context = self.build_context(check)
            except CommandError as e:
                # This will now catch our new Safety Exception
                print(f"  ❌ {e}")
                return False

        if not context.strip():
            print("\n  ⏭️  Skipped Check (No context available)\n")
            return True

        full_message = f"{prompt_def.text}\n\n{context}"

        # 2. Handle Traceability (Req 1: Debug Dump)
        self.debugger.dump_request(check_id, full_message)

        provider = self.provider_factory.get_provider(check.model)

        if logger.isEnabledFor(logging.DEBUG):
            metadata = provider.get_metadata(check.model)
            self._print_debug_info(metadata, full_message)

        print("  🤖 Analyzing...")
        raw_response = provider.analyze(check.model, full_message)

        result = self._parse_json_response(raw_response)
        status = result.get("status", "FAIL").upper()
        reason = result.get("reason", "No reason provided")

        if logger.isEnabledFor(logging.DEBUG):
            print("-" * 80)

        symbol = "✔" if status == "PASS" else "✘"
        color = "\033[92m" if status == "PASS" else "\033[91m"
        reset = "\033[0m"

        print(f"{color}{symbol} {status}{reset} | Reason: {reason}\n")

        return status == "PASS"