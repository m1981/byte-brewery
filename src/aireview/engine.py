import os
import json
import re
import logging
from typing import Dict, Any
from .domain import Config, CheckDefinition
from .services.runner import CommandRunner
from .services.providers import AIProvider
from .errors import CommandError

logger = logging.getLogger("aireview")


class ReviewEngine:
    def __init__(self, config: Config, runner: CommandRunner, ai: AIProvider):
        self.config = config
        self.runner = runner
        self.ai = ai

    def _get_empty_context_hint(self, cmd: str) -> str:
        if cmd == "internal:push_diff":
            target = os.environ.get("AI_DIFF_TARGET", "--cached")
            if target == "--cached":
                return "No staged changes found. Did you forget to `git add`?"
            return f"No changes found in range: {target}"
        if "git diff" in cmd and "--cached" in cmd:
            return "No staged changes found. Did you forget to `git add`?"
        if "git diff" in cmd:
            return "No changes found in working directory."
        return "Command returned empty output."

    def build_context(self, check: CheckDefinition) -> str:
        buffer = []
        total_chars = 0

        for ctx_id in check.context_ids:
            definition = self.config.definitions.get(ctx_id)
            if not definition:
                logger.error(f"Context ID '{ctx_id}' not found in definitions. Skipping.")
                continue

            try:
                output = self.runner.run(definition.cmd)
            except CommandError as e:
                raise e

            if not output or not output.strip():
                hint = self._get_empty_context_hint(definition.cmd)
                print(f"  ⚠️  Context '{ctx_id}' is empty. ({hint})")
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

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
            if "FAIL" in response.upper():
                return {"status": "FAIL", "reason": "Could not parse JSON, but keyword FAIL found."}
            return {"status": "PASS", "reason": "Could not parse JSON, assumed PASS."}

    def _print_debug_info(self, metadata: Dict[str, Any], full_message: str):
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
            print("")
            return False

        if not context.strip():
            print("")
            print("  ⏭️  Skipped Check (No context available)")
            print("")
            return True

        full_message = f"{prompt_def.text}\n\n{context}"

        if logger.isEnabledFor(logging.DEBUG):
            metadata = self.ai.get_metadata(check.model)
            self._print_debug_info(metadata, full_message)

        raw_response = self.ai.analyze(check.model, full_message)

        result = self._parse_json_response(raw_response)
        status = result.get("status", "FAIL").upper()
        reason = result.get("reason", "No reason provided")

        if logger.isEnabledFor(logging.DEBUG):
            print("-" * 80)

        symbol = "✔" if status == "PASS" else "✘"
        print(f"{symbol} {status} | Reason: {reason}")
        print("")

        return status == "PASS"