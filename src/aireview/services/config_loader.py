# File: src/aireview/services/config_loader.py

import logging
import os
import yaml
from ..domain import Config, ContextDefinition, PromptDefinition, CheckDefinition
from ..const import DEFAULT_CONFIG_YAML
from ..errors import ConfigError

logger = logging.getLogger("aireview")


class ConfigLoader:
    """Responsible for loading, validating, and constructing the Config object."""

    def load(self, path: str) -> Config:
        if not os.path.exists(path):
            with open(path, 'w') as f: f.write(DEFAULT_CONFIG_YAML)

        with open(path, 'r') as f:
            try:
                data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ConfigError(f"Invalid YAML syntax: {e}")

        return self._parse(data)

    def _parse(self, data: dict[str, any]) -> Config:
        defs = self._parse_definitions(data.get('definitions', []))
        prompts = self._parse_prompts(data.get('prompts', []))
        checks = self._parse_checks(data.get('checks', []), prompts)

        self._validate_references(checks, defs)
        return Config(definitions=defs, prompts=prompts, checks=checks)

    def _parse_definitions(self, raw_defs: list) -> dict[str, ContextDefinition]:
        defs = {}
        for d in raw_defs:
            self._validate_keys(d, {'id', 'tag', 'cmd'}, "Definition")
            defs[d['id']] = ContextDefinition(d['id'], d.get('tag', d['id']), d['cmd'])
        return defs

    def _parse_prompts(self, raw_prompts: list) -> dict[str, PromptDefinition]:
        prompts = {}
        for p in raw_prompts:
            self._validate_keys(p, {'id', 'text', 'file'}, "Prompt")
            p_id = p.get('id')
            text = self._resolve_prompt_text(p)

            if "JSON" not in text:
                text += "\n\nIMPORTANT: Return your response in raw JSON format: {\"status\": \"PASS\" | \"FAIL\", \"reason\": \"...\"}"

            prompts[p_id] = PromptDefinition(id=p_id, text=text)
        return prompts

    def _resolve_prompt_text(self, p_data: dict) -> str:
        if 'file' in p_data:
            try:
                with open(p_data['file'], 'r') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to load prompt file: {e}")
                return "ERROR: Prompt file missing."
        return p_data.get('text', '')

def _parse_checks(self, raw_checks: list, prompts: dict[str, PromptDefinition]) -> list[CheckDefinition]:
        checks = []
        for c in raw_checks:
            self._validate_keys(c, {'id', 'prompt_id', 'model', 'context', 'max_chars', 'system_prompt'}, "Check")

            prompt_id = c.get('prompt_id')

            # Allow inline system_prompt for convenience (KISS)
            if not prompt_id and 'system_prompt' in c:
                virtual_id = f"inline_{c['id']}"
                prompts[virtual_id] = PromptDefinition(virtual_id, c['system_prompt'])
                prompt_id = virtual_id

            # FAIL FAST: Do not auto-create 'basic_reviewer'.
            if not prompt_id:
                raise ConfigError(f"Check '{c['id']}' is missing 'prompt_id' or 'system_prompt'.")

            if prompt_id not in prompts:
                 raise ConfigError(f"Check '{c['id']}' references undefined prompt '{prompt_id}'.")

            raw_context = c.get('context', [])
            context_ids = [raw_context] if isinstance(raw_context, str) else raw_context

            checks.append(CheckDefinition(
                id=c['id'],
                prompt_id=prompt_id,
                model=c.get('model', 'gpt-3.5-turbo'),
                context_ids=context_ids,
                max_chars=c.get('max_chars', 16000)
            ))
        return checks

    def _validate_keys(self, data: dict, valid: set, name: str):
        unknown = set(data.keys()) - valid
        if unknown:
            raise ConfigError(f"{name} has unknown keys: {unknown}. Valid: {valid}")

    def _validate_references(self, checks: list[CheckDefinition], defs: dict[str, ContextDefinition]):
        for check in checks:
            for ctx_id in check.context_ids:
                if ctx_id not in defs:
                    hint = ""
                    if ctx_id == "push_diff":
                        hint = " (You must define 'push_diff' in 'definitions' with cmd: 'internal:push_diff')"
                    raise ConfigError(f"Check '{check.id}' references unknown context ID '{ctx_id}'{hint}")