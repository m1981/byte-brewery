import subprocess
import logging
from typing import Protocol, Dict, Callable
from ..errors import CommandError
from .internal_commands import InternalCommandHandler

logger = logging.getLogger("aireview")


class CommandRunner(Protocol):
    def run(self, command: str) -> str: ...


class ShellCommandRunner:
    def __init__(self):
        self.internal_handler = InternalCommandHandler()

    def run(self, command: str) -> str:
        if not command: return ""

        if command.startswith("internal:"):
            return self.internal_handler.execute(command)

        try:
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise CommandError(f"Command failed: '{command}'\nStderr: {e.stderr}")