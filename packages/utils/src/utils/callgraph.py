#!/usr/bin/env python3
"""
callgraph — Runtime Python Call Graph Analyser
===============================================

Instruments a callable or any importable Python script at *runtime* using
``pycallgraph2`` and produces:

  * a Graphviz PNG / SVG call-graph image  (requires ``dot`` on PATH)
  * an optional JSON report of call counts and timings
  * an optional Mermaid flowchart           (no Graphviz required)

Design principles
-----------------
  * **Single responsibility** — each class owns one concern.
  * **Open / closed** — new output formats extend ``OutputStrategy``
    without touching core logic.
  * **Dependency inversion** — ``CallGraphRunner`` depends on the
    ``OutputStrategy`` ABC, not on concrete outputs.
  * **Testability** — all collaborators are injected; ``pycallgraph2``
    interaction is wrapped in ``CallGraphSession`` so tests can mock it.
  * **Graceful degradation** — if the ``dot`` binary is absent the session
    automatically falls back to ``.dot`` text output so CI never breaks.

Public API
----------
  CallGraphConfig          — validated configuration dataclass
  CallGraphSession         — thin wrapper around pycallgraph2's context manager
  GraphvizOutputStrategy   — renders via pycallgraph2 → Graphviz
  JsonOutputStrategy       — captures call data and serialises to JSON
  MermaidOutputStrategy    — produces a Mermaid LR flowchart (no deps)
  CompositeOutputStrategy  — fan-out to multiple strategies
  CallGraphRunner          — orchestrates config → session → strategy
  CallGraphAnalyser        — high-level façade (the "user-facing" class)

CLI
---
  callgraph --target mymodule.py [--output call_graph.png] [--format png|svg]
            [--include 'mypackage.*'] [--exclude 'test*']
            [--json report.json] [--mermaid diagram.md]
            [--max-depth N] [--show-stdlib]

Examples
--------
  callgraph --target myapp/main.py --output docs/graph.png
  callgraph --target myapp/main.py --mermaid docs/graph.md --format svg
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
import types
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Optional dependency guard
# ---------------------------------------------------------------------------

try:
    from pycallgraph2 import PyCallGraph, Config
    from pycallgraph2.output import GraphvizOutput
    from pycallgraph2.globbing_filter import GlobbingFilter

    _HAS_PYCALLGRAPH = True
except ImportError:  # pragma: no cover
    _HAS_PYCALLGRAPH = False
    PyCallGraph = None  # type: ignore[assignment,misc]
    Config = None  # type: ignore[assignment,misc]
    GraphvizOutput = None  # type: ignore[assignment,misc]
    GlobbingFilter = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class CallGraphError(RuntimeError):
    """Raised when the call-graph pipeline encounters a fatal problem."""


class MissingDependencyError(CallGraphError):
    """Raised when pycallgraph2 is not installed."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class CallGraphConfig:
    """Validated configuration for a call-graph run.

    Attributes
    ----------
    output_path:
        Destination file for the rendered graph image.
    output_format:
        Image format accepted by Graphviz (``'png'``, ``'svg'``, …).
        Automatically downgraded to ``'dot'`` when the ``dot`` binary is
        absent (e.g. in CI).
    include_patterns:
        Glob patterns for functions to **include** (default: ``['*']``).
    exclude_patterns:
        Glob patterns for functions to **exclude**.
    max_depth:
        Maximum call-stack depth to trace.
    show_stdlib:
        When *True*, include Python standard-library frames.
    json_path:
        Optional path to write a JSON call-data report.
    mermaid_path:
        Optional path to write a Mermaid flowchart.
    """

    output_path: Path = Path("call_graph.png")
    output_format: str = "png"
    include_patterns: list[str] = field(default_factory=lambda: ["*"])
    exclude_patterns: list[str] = field(
        default_factory=lambda: ["pycallgraph.*", "pytest*", "_pytest*"]
    )
    max_depth: int = 99_999
    show_stdlib: bool = False
    json_path: Path | None = None
    mermaid_path: Path | None = None

    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        self.output_path = Path(self.output_path)
        if self.output_format not in {"png", "svg", "pdf", "dot"}:
            raise ValueError(
                f"Unsupported format '{self.output_format}'. "
                "Choose from: png, svg, pdf, dot"
            )
        if self.max_depth < 1:
            raise ValueError("max_depth must be ≥ 1")

    # ------------------------------------------------------------------
    def effective_format(self) -> str:
        """Return the format to actually use.

        Falls back to ``'dot'`` (plain text) when the ``dot`` binary is not
        found on PATH so the session never raises a hard error in CI.
        """
        if self.output_format == "dot":
            return "dot"
        if shutil.which("dot") is None:
            warnings.warn(
                "Graphviz 'dot' binary not found on PATH — "
                f"falling back from '{self.output_format}' to 'dot' (text) output. "
                "Install Graphviz to generate image output.",
                RuntimeWarning,
                stacklevel=3,
            )
            return "dot"
        return self.output_format

    # ------------------------------------------------------------------
    def effective_output_path(self) -> Path:
        """Return the output path, adjusting the suffix when falling back to dot."""
        fmt = self.effective_format()
        if fmt == "dot" and self.output_format != "dot":
            return self.output_path.with_suffix(".dot")
        return self.output_path

    # ------------------------------------------------------------------
    def build_exclude_list(self) -> list[str]:
        """Return the effective exclude list, adding stdlib exclusions when needed."""
        patterns = list(self.exclude_patterns)
        if not self.show_stdlib:
            patterns += [
                "threading.*",
                "importlib.*",
                "abc.*",
                "os.*",
                "sys.*",
                "pathlib.*",
                "io.*",
                "collections.*",
                "functools.*",
                "types.*",
                "typing.*",
                "dataclasses.*",
                "enum.*",
                "re.*",
                "json.*",
                "logging.*",
                "warnings.*",
                "copy.*",
                "weakref.*",
                "codecs.*",
            ]
        return patterns


# ---------------------------------------------------------------------------
# Call data snapshot (what we capture from the tracer)
# ---------------------------------------------------------------------------


@dataclass
class CallRecord:
    """Immutable snapshot of one traced function's statistics."""

    name: str
    call_count: int
    time_total: float
    callers: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Output strategies (Strategy pattern)
# ---------------------------------------------------------------------------


class OutputStrategy(ABC):
    """Abstract base for all call-graph output strategies."""

    @abstractmethod
    def generate(self, records: list[CallRecord], config: CallGraphConfig) -> None:
        """Produce output from *records* according to *config*."""


class GraphvizOutputStrategy(OutputStrategy):
    """Renders the call graph to an image file via ``pycallgraph2``'s
    built-in Graphviz output.

    This strategy is a thin façade; the actual ``PyCallGraph`` context
    manager is driven by ``CallGraphSession``, which calls ``generate()``
    after the trace.  The ``records`` argument is therefore unused here —
    the Graphviz output has already been written to disk by the time we
    are called.  We keep the method for interface consistency and to allow
    post-processing hooks.
    """

    def __init__(self, graphviz_output: Any | None = None) -> None:
        """
        Parameters
        ----------
        graphviz_output:
            A pre-configured ``GraphvizOutput`` instance.  Useful for
            testing (inject a mock).  When *None*, the instance is built
            by ``CallGraphSession``.
        """
        self._graphviz_output = graphviz_output

    def generate(self, records: list[CallRecord], config: CallGraphConfig) -> None:
        # The image was already rendered by pycallgraph2's own output handler.
        # We just surface a friendly confirmation message.
        print(f"[callgraph] Graph written → {config.effective_output_path()}")


class JsonOutputStrategy(OutputStrategy):
    """Serialises call records to a JSON file."""

    def generate(self, records: list[CallRecord], config: CallGraphConfig) -> None:
        if config.json_path is None:
            return
        data = [
            {
                "name": r.name,
                "call_count": r.call_count,
                "time_total": round(r.time_total, 6),
                "callers": r.callers,
            }
            for r in sorted(records, key=lambda r: r.call_count, reverse=True)
        ]
        config.json_path.write_text(
            json.dumps({"call_graph": data}, indent=2), encoding="utf-8"
        )
        print(f"[callgraph] JSON report  → {config.json_path}")


class MermaidOutputStrategy(OutputStrategy):
    """Produces a Mermaid LR flowchart from the call records.

    Requires **no** external tools — pure Python string generation.
    Ideal when Graphviz is not available.
    """

    _MAX_NODES = 150  # guard against enormous graphs

    def generate(self, records: list[CallRecord], config: CallGraphConfig) -> None:
        if config.mermaid_path is None:
            return

        lines = ["```mermaid", "flowchart LR"]
        edges_seen: set[tuple[str, str]] = set()
        node_count = 0

        for record in records:
            if node_count >= self._MAX_NODES:
                break
            callee_id = self._node_id(record.name)
            callee_label = self._short_label(record.name, record.call_count)
            lines.append(f'    {callee_id}["{callee_label}"]')
            node_count += 1

            for caller in record.callers:
                edge = (self._node_id(caller), callee_id)
                if edge not in edges_seen:
                    edges_seen.add(edge)
                    lines.append(f"    {edge[0]} --> {edge[1]}")

        lines.append("```")
        config.mermaid_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[callgraph] Mermaid chart → {config.mermaid_path}")

    # ------------------------------------------------------------------
    @staticmethod
    def _node_id(name: str) -> str:
        """Convert a dotted name to a safe Mermaid node identifier."""
        return name.replace(".", "_").replace("<", "").replace(">", "").replace(" ", "_")

    @staticmethod
    def _short_label(name: str, count: int) -> str:
        """Human-readable label: last two segments + call count."""
        parts = name.split(".")
        short = ".".join(parts[-2:]) if len(parts) > 1 else name
        return f"{short} ×{count}"


class CompositeOutputStrategy(OutputStrategy):
    """Fan-out: delegates to multiple strategies in order."""

    def __init__(self, strategies: list[OutputStrategy]) -> None:
        self._strategies = strategies

    def generate(self, records: list[CallRecord], config: CallGraphConfig) -> None:
        for strategy in self._strategies:
            strategy.generate(records, config)


# ---------------------------------------------------------------------------
# Call-graph session (wraps pycallgraph2)
# ---------------------------------------------------------------------------


class CallGraphSession:
    """Manages the ``pycallgraph2`` tracing lifecycle.

    Responsibilities
    ----------------
    * Build a ``PyCallGraph`` context manager from a ``CallGraphConfig``.
    * Run the target callable inside the context.
    * Extract ``CallRecord`` snapshots from the tracer's processor.
    * Delegate to the ``OutputStrategy`` for final output.

    Graceful degradation
    --------------------
    If the ``dot`` binary is missing, the session automatically switches to
    plain ``.dot`` text output so the pipeline never hard-crashes in CI.

    This class is the *only* place that touches ``pycallgraph2`` directly,
    making the rest of the codebase fully testable without the library.
    """

    def __init__(
        self,
        config: CallGraphConfig,
        strategy: OutputStrategy,
    ) -> None:
        self._config = config
        self._strategy = strategy

    # ------------------------------------------------------------------
    def run(self, target: Callable[[], Any]) -> list[CallRecord]:
        """Trace *target()* and return the collected ``CallRecord`` list."""
        if not _HAS_PYCALLGRAPH:
            raise MissingDependencyError(
                "pycallgraph2 is not installed. "
                "Run: uv add pycallgraph2 setuptools"
            )

        effective_fmt = self._config.effective_format()
        effective_path = self._config.effective_output_path()

        graphviz_out = GraphvizOutput(
            output_file=str(effective_path),
            output_type=effective_fmt,
        )

        pcg_config = Config(
            max_depth=self._config.max_depth,
            include_stdlib=self._config.show_stdlib,
            trace_filter=GlobbingFilter(
                include=self._config.include_patterns,
                exclude=self._config.build_exclude_list(),
            ),
        )

        pcg = PyCallGraph(output=graphviz_out, config=pcg_config)
        with pcg:
            target()

        records = self._extract_records(pcg)
        self._strategy.generate(records, self._config)
        return records

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_records(pcg: Any) -> list[CallRecord]:
        """Pull call statistics out of the tracer processor."""
        processor = pcg.tracer.processor
        func_count: dict[str, int] = dict(processor.func_count)
        func_time: dict[str, float] = dict(processor.func_time)
        call_dict: dict[str, dict[str, int]] = {
            caller: dict(callees)
            for caller, callees in processor.call_dict.items()
        }

        # Build callers index: callee → list of callers
        callers_of: dict[str, list[str]] = {}
        for caller, callees in call_dict.items():
            for callee in callees:
                callers_of.setdefault(callee, []).append(caller)

        records: list[CallRecord] = []
        for name, count in func_count.items():
            records.append(
                CallRecord(
                    name=name,
                    call_count=count,
                    time_total=func_time.get(name, 0.0),
                    callers=callers_of.get(name, []),
                )
            )
        return records


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


class CallGraphRunner:
    """Orchestrates config → session → strategy.

    Parameters
    ----------
    config:
        Validated ``CallGraphConfig``.
    session_factory:
        Callable that returns a ``CallGraphSession``-compatible object.
        Defaults to ``CallGraphSession``.  Inject a mock in tests.
    """

    def __init__(
        self,
        config: CallGraphConfig,
        session_factory: Callable[
            [CallGraphConfig, OutputStrategy], Any
        ] = CallGraphSession,
    ) -> None:
        self._config = config
        self._session_factory = session_factory

    # ------------------------------------------------------------------
    def run(self, target: Callable[[], Any]) -> list[CallRecord]:
        """Profile *target* and write all configured outputs."""
        strategies: list[OutputStrategy] = [GraphvizOutputStrategy()]
        if self._config.json_path:
            strategies.append(JsonOutputStrategy())
        if self._config.mermaid_path:
            strategies.append(MermaidOutputStrategy())

        composite = CompositeOutputStrategy(strategies)
        session = self._session_factory(self._config, composite)
        return session.run(target)


# ---------------------------------------------------------------------------
# High-level façade
# ---------------------------------------------------------------------------


class CallGraphAnalyser:
    """User-facing façade — the one class most callers should use.

    Usage
    -----
    ::

        analyser = CallGraphAnalyser(
            output="docs/graph.png",
            include=["mypackage.*"],
            exclude=["test*"],
            json_path="docs/report.json",
            mermaid_path="docs/graph.md",
        )
        analyser.profile(my_function)

    Or as a decorator::

        @analyser.decorator
        def my_function():
            ...
    """

    def __init__(
        self,
        output: str | Path = "call_graph.png",
        output_format: str = "png",
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        max_depth: int = 99_999,
        show_stdlib: bool = False,
        json_path: str | Path | None = None,
        mermaid_path: str | Path | None = None,
        *,
        runner_factory: Callable[[CallGraphConfig], CallGraphRunner] | None = None,
    ) -> None:
        self._config = CallGraphConfig(
            output_path=Path(output),
            output_format=output_format,
            include_patterns=include or ["*"],
            exclude_patterns=exclude
            or ["pycallgraph.*", "pytest*", "_pytest*"],
            max_depth=max_depth,
            show_stdlib=show_stdlib,
            json_path=Path(json_path) if json_path else None,
            mermaid_path=Path(mermaid_path) if mermaid_path else None,
        )
        self._runner_factory = runner_factory or CallGraphRunner

    # ------------------------------------------------------------------
    def profile(self, target: Callable[[], Any]) -> list[CallRecord]:
        """Run *target* under the call-graph tracer and write outputs."""
        runner = self._runner_factory(self._config)
        return runner.run(target)

    # ------------------------------------------------------------------
    def decorator(self, fn: Callable) -> Callable:
        """Use the analyser as a decorator."""
        import functools

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result: list[Any] = []

            def _call() -> None:
                result.append(fn(*args, **kwargs))

            self.profile(_call)
            return result[0] if result else None

        return wrapper

    # ------------------------------------------------------------------
    @property
    def config(self) -> CallGraphConfig:
        return self._config


# ---------------------------------------------------------------------------
# Project environment detection + re-exec
# ---------------------------------------------------------------------------


def _find_project_root(start: Path) -> Path | None:
    """Walk up from *start* to find a directory with ``pyproject.toml`` or
    ``setup.py``.  Returns the project root or ``None``."""
    current = start.resolve()
    while True:
        if (current / "pyproject.toml").exists() or (current / "setup.py").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _find_project_python(project_root: Path) -> Path | None:
    """Return the Python interpreter inside *project_root*'s venv, or ``None``."""
    for candidate in (
        project_root / ".venv" / "bin" / "python",
        project_root / ".venv" / "bin" / "python3",
        project_root / "venv" / "bin" / "python",
        project_root / "venv" / "bin" / "python3",
    ):
        if candidate.exists():
            return candidate
    return None


def _reexec_with_project_python(project_python: Path, script: Path) -> None:
    """Replace the current process with the same callgraph command re-run
    under *project_python*.

    ``pycallgraph2`` and this module's source are made importable by
    prepending their directories to ``PYTHONPATH`` before the exec, so
    the project's Python can find them even though they live in byte-utils'
    own venv.

    This is the correct fix for Python version mismatches: C-extension
    packages (pydantic-core, grpcio, etc.) are compiled per Python ABI and
    cannot be loaded by a different interpreter version.  Running everything
    under the project's own interpreter avoids the mismatch entirely.
    """
    import subprocess

    # Directories to expose to the re-exec'd interpreter via PYTHONPATH:
    #  1. callgraph's own src dir  →  so `from utils.callgraph import …` works
    #  2. pycallgraph2's location  →  it lives in byte-utils' venv, not the project venv
    extra_paths: list[str] = []

    callgraph_src = Path(__file__).resolve().parent.parent  # …/packages/utils/src
    extra_paths.append(str(callgraph_src))

    try:
        import pycallgraph2 as _pcg
        pcg_path = str(Path(_pcg.__file__).resolve().parent.parent)
        extra_paths.append(pcg_path)
    except ImportError:
        pass

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in [*extra_paths, existing_pythonpath] if p
    )
    # Signal that we have already re-exec'd so the child does not loop.
    env["_CALLGRAPH_REEXEC"] = "1"

    cmd = [str(project_python), Path(__file__).resolve()] + sys.argv[1:]
    print(
        f"[callgraph] Python mismatch — re-running under project interpreter: "
        f"{project_python}",
        file=sys.stderr,
    )
    result = subprocess.run(cmd, env=env)
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# Module loader helper (used by CLI)
# ---------------------------------------------------------------------------


def _load_and_run_module(script_path: Path) -> None:
    """Import *script_path* as ``__main__`` and execute it."""
    spec = importlib.util.spec_from_file_location("__main__", script_path)
    if spec is None or spec.loader is None:
        raise CallGraphError(f"Cannot load module from '{script_path}'")
    mod = types.ModuleType("__main__")
    mod.__file__ = str(script_path)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="callgraph",
        description=(
            "Profile a Python script or callable and generate a visual call graph.\n\n"
            "Requires pycallgraph2 + Graphviz (for image output).\n"
            "Mermaid output works without Graphviz."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  callgraph --target myapp/main.py
  callgraph --target myapp/main.py --output docs/graph.svg --format svg
  callgraph --target myapp/main.py --include 'mypackage.*' --exclude 'test*'
  callgraph --target myapp/main.py --json report.json --mermaid graph.md
  callgraph --target myapp/main.py --max-depth 5 --show-stdlib
        """,
    )
    parser.add_argument(
        "--target", "-t",
        required=True,
        metavar="SCRIPT",
        help="Python script to profile (e.g. myapp/main.py)",
    )
    parser.add_argument(
        "--output", "-o",
        default="call_graph.png",
        metavar="FILE",
        help="Output image path (default: call_graph.png)",
    )
    parser.add_argument(
        "--format", "-f",
        dest="output_format",
        default="png",
        choices=["png", "svg", "pdf", "dot"],
        help="Output image format (default: png)",
    )
    parser.add_argument(
        "--include",
        nargs="*",
        default=["*"],
        metavar="PATTERN",
        help="Glob patterns to include (default: '*')",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        metavar="PATTERN",
        help="Glob patterns to exclude",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=99_999,
        metavar="N",
        help="Maximum call-stack depth (default: unlimited)",
    )
    parser.add_argument(
        "--show-stdlib",
        action="store_true",
        help="Include Python standard-library frames",
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        default=None,
        metavar="FILE",
        help="Write call data to a JSON file",
    )
    parser.add_argument(
        "--mermaid",
        dest="mermaid_path",
        default=None,
        metavar="FILE",
        help="Write a Mermaid flowchart (.md) — no Graphviz needed",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    script = Path(args.target).resolve()
    if not script.exists():
        print(f"Error: '{script}' not found.", file=sys.stderr)
        sys.exit(1)

    # ── Python version / venv mismatch guard ────────────────────────────
    # callgraph runs inside byte-utils' own uv-tool venv.  If the target
    # project uses a *different* Python version its C-extension packages
    # (pydantic-core, grpcio, …) are compiled for that version's ABI and
    # cannot be imported by our interpreter.  Detect this early and
    # transparently re-exec the entire command under the project's own
    # Python so everything runs in the right interpreter + venv.
    if not os.environ.get("_CALLGRAPH_REEXEC"):
        project_root = _find_project_root(script.parent)
        if project_root is not None:
            project_python = _find_project_python(project_root)
            if project_python is not None and str(project_python) != sys.executable:
                _reexec_with_project_python(project_python, script)
                # _reexec_with_project_python calls sys.exit() — never reached
    # ────────────────────────────────────────────────────────────────────

    # Add the project root and script directory to sys.path.
    # Projects that use absolute "src.*" imports (e.g. `from src.foo import bar`)
    # expect the project root (parent of src/) on sys.path.  Projects with a
    # flat layout expect the script's own directory.  We add both.
    project_root_for_path = _find_project_root(script.parent)
    if project_root_for_path is not None:
        root_str = str(project_root_for_path)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)
    script_dir_str = str(script.parent)
    if script_dir_str not in sys.path:
        sys.path.insert(0, script_dir_str)

    analyser = CallGraphAnalyser(
        output=args.output,
        output_format=args.output_format,
        include=args.include,
        exclude=args.exclude or ["pycallgraph.*", "pytest*", "_pytest*"],
        max_depth=args.max_depth,
        show_stdlib=args.show_stdlib,
        json_path=args.json_path,
        mermaid_path=args.mermaid_path,
    )

    try:
        analyser.profile(lambda: _load_and_run_module(script))
    except CallGraphError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
