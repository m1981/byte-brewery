#!/usr/bin/env python3
"""
ignore_utils.py
Shared utility for parsing .gitignore files and filtering paths.
"""

import os
import fnmatch
from pathlib import Path
from typing import List, Union


class GitignoreParser:
    """Parser for .gitignore files to determine which files to skip."""

    # Default patterns to ignore even if not in .gitignore
    COMMON_PATTERNS = [
        '.git', '.venv', 'venv', 'env', '__pycache__',
        '*.pyc', '*.pyo', '*.pyd', '.Python', 'build', 'dist',
        'node_modules', '.svelte-kit', '.next', '.nuxt',  # Added JS/Svelte defaults
        '.idea', '.vscode', '.DS_Store', 'coverage'
    ]

    def __init__(self, project_dir: Union[str, Path]):
        self.project_dir = Path(project_dir).resolve()
        self.ignore_patterns = self._load_gitignore()

    def _load_gitignore(self) -> List[str]:
        """Load patterns from .gitignore file and combine with defaults."""
        patterns = list(self.COMMON_PATTERNS)
        gitignore_path = self.project_dir / '.gitignore'

        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Normalize patterns
                            if line.startswith('/'):
                                line = line[1:]
                            if line.endswith('/'):
                                line = line + '*'  # Handle dir syntax
                            patterns.append(line)
            except IOError:
                pass  # Fail silently if unreadable

        return patterns

    def should_ignore(self, path: Union[str, Path]) -> bool:
        """Check if a path should be ignored."""
        # Convert to Path object relative to project root
        try:
            abs_path = Path(path).resolve()
            rel_path = abs_path.relative_to(self.project_dir)
        except ValueError:
            # Path is not inside project_dir
            return True

        path_str = str(rel_path)
        name = rel_path.name

        # 1. Always ignore hidden files/dirs (Unix standard)
        if name.startswith('.') and name != '.gitignore':
            return True

        # 2. Check against patterns
        for pattern in self.ignore_patterns:
            # Match exact file or directory name
            if fnmatch.fnmatch(name, pattern):
                return True
            # Match relative path (e.g., src/temp/*)
            if fnmatch.fnmatch(path_str, pattern):
                return True

            # Check path parts for directory matches
            # (e.g. pattern 'node_modules' should match 'subdir/node_modules/file.js')
            for part in rel_path.parts:
                if fnmatch.fnmatch(part, pattern):
                    return True

        return False