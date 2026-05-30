"""
Tests for utils.callgraph
=========================

TDD order:
  1. CallGraphConfig — validation, defaults, exclude-list, graceful degradation
  2. CallRecord      — dataclass construction
  3. MermaidOutputStrategy — pure-Python renderer (no pycallgraph2 needed)
  4. JsonOutputStrategy    — JSON serialisation
  5. GraphvizOutputStrategy — smoke test (no graphviz binary needed)
  6. CompositeOutputStrategy — fan-out delegation
  7. CallGraphSession       — pycallgraph2 interaction via mock
  8. CallGraphRunner        — wiring config→session→strategy
  9. CallGraphAnalyser      — façade, profile(), decorator()
  10. CLI arg parser        — build_parser()
  11. Integration           — real pycallgraph2 trace over a tiny target
"""

from __future__ import annotations

import json
import shutil
import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from utils.callgraph import (
    CallGraphAnalyser,
    CallGraphConfig,
    CallGraphError,
    CallGraphRunner,
    CallGraphSession,
    CallRecord,
    CompositeOutputStrategy,
    GraphvizOutputStrategy,
    JsonOutputStrategy,
    MermaidOutputStrategy,
    MissingDependencyError,
    OutputStrategy,
    build_parser,
)


# ===========================================================================
# Helpers / fixtures
# ===========================================================================


def _make_records(n: int = 3) -> list[CallRecord]:
    """Return *n* dummy CallRecords for output-strategy tests."""
    return [
        CallRecord(
            name=f"mypackage.module{i}.func_{i}",
            call_count=i + 1,
            time_total=0.001 * (i + 1),
            callers=[f"mypackage.caller{i}"] if i > 0 else [],
        )
        for i in range(n)
    ]


def _make_config(**kwargs) -> CallGraphConfig:
    return CallGraphConfig(**kwargs)


# ===========================================================================
# 1. CallGraphConfig
# ===========================================================================


class TestCallGraphConfig:
    def test_defaults(self):
        cfg = CallGraphConfig()
        assert cfg.output_path == Path("call_graph.png")
        assert cfg.output_format == "png"
        assert cfg.include_patterns == ["*"]
        assert cfg.max_depth == 99_999
        assert cfg.show_stdlib is False
        assert cfg.json_path is None
        assert cfg.mermaid_path is None

    def test_output_path_coerced_to_path(self):
        cfg = CallGraphConfig(output_path="some/dir/graph.svg", output_format="svg")
        assert isinstance(cfg.output_path, Path)
        assert cfg.output_path == Path("some/dir/graph.svg")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            CallGraphConfig(output_format="bmp")

    def test_valid_formats_accepted(self):
        for fmt in ("png", "svg", "pdf", "dot"):
            cfg = CallGraphConfig(output_format=fmt)
            assert cfg.output_format == fmt

    def test_max_depth_zero_raises(self):
        with pytest.raises(ValueError, match="max_depth"):
            CallGraphConfig(max_depth=0)

    def test_max_depth_negative_raises(self):
        with pytest.raises(ValueError, match="max_depth"):
            CallGraphConfig(max_depth=-5)

    def test_max_depth_one_accepted(self):
        cfg = CallGraphConfig(max_depth=1)
        assert cfg.max_depth == 1

    def test_json_path_accepted(self, tmp_path):
        cfg = CallGraphConfig(json_path=tmp_path / "report.json")
        assert cfg.json_path == tmp_path / "report.json"

    def test_mermaid_path_accepted(self, tmp_path):
        cfg = CallGraphConfig(mermaid_path=tmp_path / "graph.md")
        assert cfg.mermaid_path == tmp_path / "graph.md"

    def test_build_exclude_list_hides_stdlib_by_default(self):
        cfg = CallGraphConfig()
        excludes = cfg.build_exclude_list()
        assert "os.*" in excludes
        assert "sys.*" in excludes
        assert "threading.*" in excludes

    def test_build_exclude_list_show_stdlib(self):
        cfg = CallGraphConfig(show_stdlib=True)
        excludes = cfg.build_exclude_list()
        assert "os.*" not in excludes
        assert "sys.*" not in excludes

    def test_build_exclude_list_always_includes_custom_excludes(self):
        cfg = CallGraphConfig(exclude_patterns=["my_noisy_lib.*"])
        excludes = cfg.build_exclude_list()
        assert "my_noisy_lib.*" in excludes

    def test_build_exclude_list_always_includes_pycallgraph(self):
        cfg = CallGraphConfig(exclude_patterns=["pycallgraph.*"])
        excludes = cfg.build_exclude_list()
        assert "pycallgraph.*" in excludes

    # -- graceful degradation -----------------------------------------------

    def test_effective_format_returns_dot_when_graphviz_absent(self):
        cfg = CallGraphConfig(output_format="png")
        with patch("utils.callgraph.shutil.which", return_value=None):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                fmt = cfg.effective_format()
            assert fmt == "dot"
            assert any("dot" in str(warning.message).lower() for warning in w)

    def test_effective_format_returns_requested_when_graphviz_present(self):
        cfg = CallGraphConfig(output_format="svg")
        with patch("utils.callgraph.shutil.which", return_value="/usr/bin/dot"):
            assert cfg.effective_format() == "svg"

    def test_effective_format_dot_always_returns_dot(self):
        cfg = CallGraphConfig(output_format="dot")
        # Even without graphviz dot binary, 'dot' format is always valid text
        assert cfg.effective_format() == "dot"

    def test_effective_output_path_changes_suffix_on_fallback(self):
        cfg = CallGraphConfig(output_path="graph.png", output_format="png")
        with patch("utils.callgraph.shutil.which", return_value=None):
            p = cfg.effective_output_path()
        assert p.suffix == ".dot"

    def test_effective_output_path_unchanged_when_graphviz_present(self):
        cfg = CallGraphConfig(output_path="graph.png", output_format="png")
        with patch("utils.callgraph.shutil.which", return_value="/usr/bin/dot"):
            p = cfg.effective_output_path()
        assert p.suffix == ".png"


# ===========================================================================
# 2. CallRecord
# ===========================================================================


class TestCallRecord:
    def test_construction_minimal(self):
        r = CallRecord(name="a.b.c", call_count=5, time_total=0.01)
        assert r.name == "a.b.c"
        assert r.call_count == 5
        assert r.time_total == 0.01
        assert r.callers == []

    def test_construction_with_callers(self):
        r = CallRecord(name="x.y", call_count=1, time_total=0.0, callers=["root"])
        assert r.callers == ["root"]

    def test_dataclass_equality(self):
        r1 = CallRecord(name="f", call_count=1, time_total=0.0)
        r2 = CallRecord(name="f", call_count=1, time_total=0.0)
        assert r1 == r2

    def test_dataclass_inequality(self):
        r1 = CallRecord(name="f", call_count=1, time_total=0.0)
        r2 = CallRecord(name="g", call_count=1, time_total=0.0)
        assert r1 != r2


# ===========================================================================
# 3. MermaidOutputStrategy
# ===========================================================================


class TestMermaidOutputStrategy:
    def test_no_op_when_mermaid_path_is_none(self, tmp_path):
        cfg = CallGraphConfig()  # mermaid_path=None
        strategy = MermaidOutputStrategy()
        strategy.generate(_make_records(), cfg)
        # no file written, no error

    def test_writes_mermaid_file(self, tmp_path):
        out = tmp_path / "graph.md"
        cfg = CallGraphConfig(mermaid_path=out)
        records = _make_records(3)
        MermaidOutputStrategy().generate(records, cfg)
        assert out.exists()
        content = out.read_text()
        assert "```mermaid" in content
        assert "flowchart LR" in content

    def test_contains_node_for_each_record(self, tmp_path):
        out = tmp_path / "graph.md"
        cfg = CallGraphConfig(mermaid_path=out)
        records = _make_records(2)
        MermaidOutputStrategy().generate(records, cfg)
        content = out.read_text()
        assert "func_0" in content
        assert "func_1" in content

    def test_contains_edges_for_callers(self, tmp_path):
        out = tmp_path / "graph.md"
        cfg = CallGraphConfig(mermaid_path=out)
        records = [
            CallRecord(name="pkg.parent", call_count=1, time_total=0.0),
            CallRecord(name="pkg.child", call_count=2, time_total=0.0, callers=["pkg.parent"]),
        ]
        MermaidOutputStrategy().generate(records, cfg)
        content = out.read_text()
        assert "-->" in content

    def test_node_id_replaces_dots(self):
        node_id = MermaidOutputStrategy._node_id("a.b.c")
        assert "." not in node_id
        assert node_id == "a_b_c"

    def test_short_label_two_segments(self):
        label = MermaidOutputStrategy._short_label("a.b.c", 7)
        assert "b.c" in label
        assert "×7" in label

    def test_short_label_single_segment(self):
        label = MermaidOutputStrategy._short_label("func", 3)
        assert "func" in label
        assert "×3" in label

    def test_empty_records_produces_valid_mermaid(self, tmp_path):
        out = tmp_path / "graph.md"
        cfg = CallGraphConfig(mermaid_path=out)
        MermaidOutputStrategy().generate([], cfg)
        content = out.read_text()
        assert "```mermaid" in content
        assert "```" in content

    def test_max_nodes_guard(self, tmp_path):
        """Strategy must not crash or produce enormous output for 200+ records."""
        out = tmp_path / "graph.md"
        cfg = CallGraphConfig(mermaid_path=out)
        records = [
            CallRecord(name=f"pkg.func_{i}", call_count=1, time_total=0.0)
            for i in range(200)
        ]
        MermaidOutputStrategy().generate(records, cfg)
        content = out.read_text()
        assert content.count("[") <= MermaidOutputStrategy._MAX_NODES + 5


# ===========================================================================
# 4. JsonOutputStrategy
# ===========================================================================


class TestJsonOutputStrategy:
    def test_no_op_when_json_path_is_none(self):
        cfg = CallGraphConfig()
        JsonOutputStrategy().generate(_make_records(), cfg)

    def test_writes_json_file(self, tmp_path):
        out = tmp_path / "report.json"
        cfg = CallGraphConfig(json_path=out)
        records = _make_records(3)
        JsonOutputStrategy().generate(records, cfg)
        assert out.exists()
        data = json.loads(out.read_text())
        assert "call_graph" in data

    def test_json_schema(self, tmp_path):
        out = tmp_path / "report.json"
        cfg = CallGraphConfig(json_path=out)
        records = [CallRecord(name="a.b", call_count=5, time_total=0.123, callers=["root"])]
        JsonOutputStrategy().generate(records, cfg)
        data = json.loads(out.read_text())
        entry = data["call_graph"][0]
        assert entry["name"] == "a.b"
        assert entry["call_count"] == 5
        assert entry["callers"] == ["root"]
        assert isinstance(entry["time_total"], float)

    def test_sorted_by_call_count_descending(self, tmp_path):
        out = tmp_path / "report.json"
        cfg = CallGraphConfig(json_path=out)
        records = [
            CallRecord(name="low", call_count=1, time_total=0.0),
            CallRecord(name="high", call_count=99, time_total=0.0),
            CallRecord(name="mid", call_count=10, time_total=0.0),
        ]
        JsonOutputStrategy().generate(records, cfg)
        data = json.loads(out.read_text())
        counts = [e["call_count"] for e in data["call_graph"]]
        assert counts == sorted(counts, reverse=True)

    def test_empty_records(self, tmp_path):
        out = tmp_path / "report.json"
        cfg = CallGraphConfig(json_path=out)
        JsonOutputStrategy().generate([], cfg)
        data = json.loads(out.read_text())
        assert data["call_graph"] == []


# ===========================================================================
# 5. GraphvizOutputStrategy
# ===========================================================================


class TestGraphvizOutputStrategy:
    def test_generate_prints_confirmation(self, capsys, tmp_path):
        cfg = CallGraphConfig(output_path=tmp_path / "g.png")
        with patch("utils.callgraph.shutil.which", return_value="/usr/bin/dot"):
            GraphvizOutputStrategy().generate([], cfg)
        out = capsys.readouterr().out
        assert "Graph written" in out

    def test_accepts_injected_graphviz_output(self):
        mock_out = MagicMock()
        strategy = GraphvizOutputStrategy(graphviz_output=mock_out)
        cfg = CallGraphConfig()
        strategy.generate([], cfg)  # should not raise


# ===========================================================================
# 6. CompositeOutputStrategy
# ===========================================================================


class TestCompositeOutputStrategy:
    def _make_mock_strategy(self) -> OutputStrategy:
        m = MagicMock(spec=OutputStrategy)
        return m

    def test_delegates_to_all_strategies(self):
        s1 = self._make_mock_strategy()
        s2 = self._make_mock_strategy()
        composite = CompositeOutputStrategy([s1, s2])
        records = _make_records(2)
        cfg = CallGraphConfig()
        composite.generate(records, cfg)
        s1.generate.assert_called_once_with(records, cfg)
        s2.generate.assert_called_once_with(records, cfg)

    def test_empty_strategies_list_is_no_op(self):
        composite = CompositeOutputStrategy([])
        composite.generate([], CallGraphConfig())  # must not raise

    def test_order_preserved(self):
        calls = []

        class _OrderCapture(OutputStrategy):
            def __init__(self, tag):
                self.tag = tag

            def generate(self, records, config):
                calls.append(self.tag)

        composite = CompositeOutputStrategy([_OrderCapture("A"), _OrderCapture("B")])
        composite.generate([], CallGraphConfig())
        assert calls == ["A", "B"]


# ===========================================================================
# 7. CallGraphSession — mock pycallgraph2
# ===========================================================================


class _FakeProcessor:
    """Minimal fake of pycallgraph2's TraceProcessor."""

    func_count = {"mod.a": 3, "mod.b": 1, "__main__": 1}
    func_time = {"mod.a": 0.05, "mod.b": 0.01, "__main__": 0.0}
    call_dict = {
        "__main__": {"mod.a": 2},
        "mod.a": {"mod.b": 1},
    }


class _FakeTracer:
    processor = _FakeProcessor()


class _FakePCG:
    """Fake context-manager wrapping a _FakeTracer."""

    tracer = _FakeTracer()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass


class TestCallGraphSession:
    @patch("utils.callgraph._HAS_PYCALLGRAPH", False)
    def test_raises_missing_dependency_when_not_installed(self):
        cfg = CallGraphConfig()
        strategy = MagicMock(spec=OutputStrategy)
        session = CallGraphSession(cfg, strategy)
        with pytest.raises(MissingDependencyError):
            session.run(lambda: None)

    def test_extract_records_returns_call_records(self):
        fake_pcg = _FakePCG()
        records = CallGraphSession._extract_records(fake_pcg)
        names = {r.name for r in records}
        assert "mod.a" in names
        assert "mod.b" in names

    def test_extract_records_counts_are_correct(self):
        fake_pcg = _FakePCG()
        records = CallGraphSession._extract_records(fake_pcg)
        by_name = {r.name: r for r in records}
        assert by_name["mod.a"].call_count == 3
        assert by_name["mod.b"].call_count == 1

    def test_extract_records_callers_are_populated(self):
        fake_pcg = _FakePCG()
        records = CallGraphSession._extract_records(fake_pcg)
        by_name = {r.name: r for r in records}
        assert "__main__" in by_name["mod.a"].callers
        assert "mod.a" in by_name["mod.b"].callers

    def test_extract_records_time_totals(self):
        fake_pcg = _FakePCG()
        records = CallGraphSession._extract_records(fake_pcg)
        by_name = {r.name: r for r in records}
        assert abs(by_name["mod.a"].time_total - 0.05) < 1e-9

    @patch("utils.callgraph.PyCallGraph")
    @patch("utils.callgraph.GraphvizOutput")
    @patch("utils.callgraph.GlobbingFilter")
    @patch("utils.callgraph.Config")
    def test_run_calls_strategy_generate(
        self, mock_config, mock_filter, mock_gviz, mock_pcg_class
    ):
        """Session.run() must call strategy.generate with extracted records."""
        fake_pcg = _FakePCG()
        mock_pcg_class.return_value = fake_pcg

        strategy = MagicMock(spec=OutputStrategy)
        cfg = CallGraphConfig()
        session = CallGraphSession(cfg, strategy)
        records = session.run(lambda: None)

        strategy.generate.assert_called_once()
        assert isinstance(records, list)
        assert all(isinstance(r, CallRecord) for r in records)


# ===========================================================================
# 8. CallGraphRunner
# ===========================================================================


class TestCallGraphRunner:
    def _make_session_factory(self, records: list[CallRecord]):
        """Returns a factory that produces a mock session returning *records*."""

        def factory(cfg, strategy):
            mock_session = MagicMock()
            mock_session.run.return_value = records
            return mock_session

        return factory

    def test_runner_returns_records(self):
        expected = _make_records(2)
        cfg = CallGraphConfig()
        runner = CallGraphRunner(cfg, session_factory=self._make_session_factory(expected))
        result = runner.run(lambda: None)
        assert result == expected

    def test_runner_adds_json_strategy_when_configured(self, tmp_path):
        cfg = CallGraphConfig(json_path=tmp_path / "r.json")
        captured_strategy: list[OutputStrategy] = []

        def factory(c, s):
            captured_strategy.append(s)
            m = MagicMock()
            m.run.return_value = []
            return m

        CallGraphRunner(cfg, session_factory=factory).run(lambda: None)
        composite = captured_strategy[0]
        assert isinstance(composite, CompositeOutputStrategy)
        assert any(isinstance(s, JsonOutputStrategy) for s in composite._strategies)

    def test_runner_adds_mermaid_strategy_when_configured(self, tmp_path):
        cfg = CallGraphConfig(mermaid_path=tmp_path / "g.md")
        captured: list[CompositeOutputStrategy] = []

        def factory(c, s):
            captured.append(s)
            m = MagicMock()
            m.run.return_value = []
            return m

        CallGraphRunner(cfg, session_factory=factory).run(lambda: None)
        assert any(isinstance(s, MermaidOutputStrategy) for s in captured[0]._strategies)

    def test_runner_always_has_graphviz_strategy(self):
        cfg = CallGraphConfig()
        captured: list[CompositeOutputStrategy] = []

        def factory(c, s):
            captured.append(s)
            m = MagicMock()
            m.run.return_value = []
            return m

        CallGraphRunner(cfg, session_factory=factory).run(lambda: None)
        assert any(isinstance(s, GraphvizOutputStrategy) for s in captured[0]._strategies)


# ===========================================================================
# 9. CallGraphAnalyser — façade
# ===========================================================================


class _MockRunner:
    """Deterministic test runner."""

    def __init__(self, records: list[CallRecord]):
        self._records = records

    def run(self, target):
        target()  # call it so side effects happen
        return self._records


class TestCallGraphAnalyser:
    def _analyser_with_mock_runner(self, records=None) -> CallGraphAnalyser:
        r = records or _make_records(2)

        def _factory(cfg):
            return _MockRunner(r)

        return CallGraphAnalyser(runner_factory=_factory)

    def test_profile_returns_records(self):
        expected = _make_records(3)
        analyser = self._analyser_with_mock_runner(expected)
        result = analyser.profile(lambda: None)
        assert result == expected

    def test_profile_calls_target(self):
        calls: list[int] = []

        def _target():
            calls.append(1)

        self._analyser_with_mock_runner().profile(_target)
        assert calls == [1]

    def test_config_property(self):
        analyser = self._analyser_with_mock_runner()
        assert isinstance(analyser.config, CallGraphConfig)

    def test_config_reflects_constructor_args(self, tmp_path):
        out = tmp_path / "g.png"
        analyser = CallGraphAnalyser(output=out, max_depth=5, runner_factory=lambda c: _MockRunner([]))
        assert analyser.config.output_path == out
        assert analyser.config.max_depth == 5

    def test_decorator_calls_function_and_returns_value(self):
        analyser = self._analyser_with_mock_runner()

        @analyser.decorator
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_decorator_preserves_function_name(self):
        analyser = self._analyser_with_mock_runner()

        @analyser.decorator
        def my_func():
            pass

        assert my_func.__name__ == "my_func"

    def test_include_patterns_passed_to_config(self):
        analyser = CallGraphAnalyser(include=["myapp.*"], runner_factory=lambda c: _MockRunner([]))
        assert analyser.config.include_patterns == ["myapp.*"]

    def test_exclude_patterns_passed_to_config(self):
        analyser = CallGraphAnalyser(exclude=["test*"], runner_factory=lambda c: _MockRunner([]))
        assert analyser.config.exclude_patterns == ["test*"]

    def test_mermaid_path_passed_to_config(self, tmp_path):
        mp = tmp_path / "graph.md"
        analyser = CallGraphAnalyser(mermaid_path=mp, runner_factory=lambda c: _MockRunner([]))
        assert analyser.config.mermaid_path == mp

    def test_json_path_passed_to_config(self, tmp_path):
        jp = tmp_path / "report.json"
        analyser = CallGraphAnalyser(json_path=jp, runner_factory=lambda c: _MockRunner([]))
        assert analyser.config.json_path == jp

    def test_show_stdlib_default_false(self):
        analyser = self._analyser_with_mock_runner()
        assert analyser.config.show_stdlib is False

    def test_show_stdlib_can_be_enabled(self):
        analyser = CallGraphAnalyser(show_stdlib=True, runner_factory=lambda c: _MockRunner([]))
        assert analyser.config.show_stdlib is True


# ===========================================================================
# 10. CLI arg parser
# ===========================================================================


class TestBuildParser:
    def test_target_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_default_output(self):
        parser = build_parser()
        args = parser.parse_args(["--target", "main.py"])
        assert args.output == "call_graph.png"

    def test_default_format(self):
        args = build_parser().parse_args(["--target", "main.py"])
        assert args.output_format == "png"

    def test_custom_output(self):
        args = build_parser().parse_args(["--target", "main.py", "--output", "out.svg"])
        assert args.output == "out.svg"

    def test_format_choices(self):
        for fmt in ("png", "svg", "pdf", "dot"):
            args = build_parser().parse_args(["--target", "main.py", "--format", fmt])
            assert args.output_format == fmt

    def test_invalid_format_exits(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(["--target", "main.py", "--format", "bmp"])

    def test_include_patterns(self):
        args = build_parser().parse_args(
            ["--target", "main.py", "--include", "myapp.*", "utils.*"]
        )
        assert args.include == ["myapp.*", "utils.*"]

    def test_exclude_patterns(self):
        args = build_parser().parse_args(
            ["--target", "main.py", "--exclude", "test*", "pytest*"]
        )
        assert args.exclude == ["test*", "pytest*"]

    def test_max_depth(self):
        args = build_parser().parse_args(["--target", "main.py", "--max-depth", "5"])
        assert args.max_depth == 5

    def test_show_stdlib_flag(self):
        args = build_parser().parse_args(["--target", "main.py", "--show-stdlib"])
        assert args.show_stdlib is True

    def test_json_path(self):
        args = build_parser().parse_args(["--target", "main.py", "--json", "r.json"])
        assert args.json_path == "r.json"

    def test_mermaid_path(self):
        args = build_parser().parse_args(["--target", "main.py", "--mermaid", "g.md"])
        assert args.mermaid_path == "g.md"

    def test_default_show_stdlib_false(self):
        args = build_parser().parse_args(["--target", "main.py"])
        assert args.show_stdlib is False

    def test_short_flags(self):
        args = build_parser().parse_args(
            ["-t", "main.py", "-o", "out.png", "-f", "png"]
        )
        assert args.target == "main.py"
        assert args.output == "out.png"


# ===========================================================================
# 11. Integration — real pycallgraph2 trace
# ===========================================================================


def _fibonacci(n: int) -> int:
    """Tiny recursive target for integration test."""
    if n <= 1:
        return n
    return _fibonacci(n - 1) + _fibonacci(n - 2)


# Skip integration tests if dot binary is not available
_dot_available = shutil.which("dot") is not None
_integration_skip = pytest.mark.skipif(
    not _dot_available,
    reason="Graphviz 'dot' binary not on PATH — integration tests skipped",
)


class TestIntegration:
    """These tests exercise the real pycallgraph2 library end-to-end."""

    @_integration_skip
    def test_profile_fibonacci_produces_records(self, tmp_path):
        """End-to-end: profile a real function, get non-empty records."""
        out_png = tmp_path / "fib.png"
        analyser = CallGraphAnalyser(
            output=out_png,
            include=["*"],
            exclude=["pycallgraph.*", "pytest*", "_pytest*"],
            max_depth=10,
        )
        records = analyser.profile(lambda: _fibonacci(5))
        assert len(records) > 0
        assert all(isinstance(r, CallRecord) for r in records)

    @_integration_skip
    def test_profile_fibonacci_call_count(self, tmp_path):
        """_fibonacci(5) calls _fibonacci 15 times total (known)."""
        out_png = tmp_path / "fib.png"
        analyser = CallGraphAnalyser(
            output=out_png,
            include=["*"],
            exclude=["pycallgraph.*", "pytest*", "_pytest*"],
            max_depth=20,
        )
        records = analyser.profile(lambda: _fibonacci(5))
        fib_record = next(
            (r for r in records if "fibonacci" in r.name or "_fibonacci" in r.name),
            None,
        )
        assert fib_record is not None, f"No fibonacci record in {[r.name for r in records]}"
        assert fib_record.call_count >= 15

    @_integration_skip
    def test_mermaid_output_written_in_integration(self, tmp_path):
        """Full pipeline: pycallgraph2 trace + Mermaid output on disk."""
        out_png = tmp_path / "fib.png"
        md_out = tmp_path / "fib.md"
        analyser = CallGraphAnalyser(
            output=out_png,
            include=["*"],
            exclude=["pycallgraph.*", "pytest*", "_pytest*"],
            mermaid_path=md_out,
        )
        analyser.profile(lambda: _fibonacci(4))
        assert md_out.exists()
        content = md_out.read_text()
        assert "```mermaid" in content

    @_integration_skip
    def test_json_output_written_in_integration(self, tmp_path):
        """Full pipeline: pycallgraph2 trace + JSON report on disk."""
        out_png = tmp_path / "fib.png"
        json_out = tmp_path / "fib.json"
        analyser = CallGraphAnalyser(
            output=out_png,
            include=["*"],
            exclude=["pycallgraph.*", "pytest*", "_pytest*"],
            json_path=json_out,
        )
        analyser.profile(lambda: _fibonacci(4))
        assert json_out.exists()
        data = json.loads(json_out.read_text())
        assert "call_graph" in data
        assert len(data["call_graph"]) > 0

    @_integration_skip
    def test_decorator_integration(self, tmp_path):
        """Decorator wrapping should still return the correct value."""
        out_png = tmp_path / "fib.png"
        analyser = CallGraphAnalyser(
            output=out_png,
            include=["*"],
            exclude=["pycallgraph.*", "pytest*", "_pytest*"],
        )

        @analyser.decorator
        def run_fib():
            return _fibonacci(4)

        result = run_fib()
        assert result == _fibonacci(4)

    @_integration_skip
    def test_image_file_is_created(self, tmp_path):
        """Graphviz must write an actual PNG file to disk."""
        out_png = tmp_path / "fib.png"
        analyser = CallGraphAnalyser(
            output=out_png,
            include=["*"],
            exclude=["pycallgraph.*", "pytest*", "_pytest*"],
        )
        analyser.profile(lambda: _fibonacci(3))
        assert out_png.exists()
        assert out_png.stat().st_size > 0
