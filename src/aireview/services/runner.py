import subprocess
import logging
from typing import Protocol, Dict, Callable, Optional, List
from ..errors import CommandError
from .internal_commands import InternalCommandHandler

logger = logging.getLogger("aireview")


class CommandRunner(Protocol):
    # Update Protocol signature
    def run(self, command: str, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> str: ...


class ShellCommandRunner:
    def __init__(self):
        self.internal_handler = InternalCommandHandler()

    def run(self, command: str, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> str:
        if not command: return ""

        if command.startswith("internal:"):
            # Pass the filters to the internal handler
            return self.internal_handler.execute(command, include, exclude)

        try:
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise CommandError(f"Command failed: '{command}'\nStderr: {e.stderr}")