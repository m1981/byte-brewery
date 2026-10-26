"""Read-only snapshot of changed-file mtimes; exploratory pilot, not app behavior.

Run with the project's Python: tools/measure_change_groups.py --output /tmp/result.json
/absolute/repo [...]. The output contains paths and timestamps, never file contents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.status import STATUS_ARGS, parse_status

THRESHOLDS = (30, 60, 120, 300, 600, 900)


def clusters(rows, gap, cap=None):
    groups = []
    known = (r for r in rows if r["mtime_ns"] is not None)
    for row in sorted(known, key=lambda r: (-r["mtime_ns"], r["path"])):
        if (not groups
                or groups[-1][-1]["mtime_ns"] - row["mtime_ns"] > gap * 10**9
                or (cap is not None
                    and groups[-1][0]["mtime_ns"] - row["mtime_ns"] > cap * 10**9)):
            groups.append([])
        groups[-1].append(row)
    return groups


def stats(rows, gap, cap=None):
    groups = clusters(rows, gap, cap)
    return {
        "groups": len(groups),
        "singletons": sum(len(g) == 1 for g in groups),
        "max_files": max(map(len, groups), default=0),
        "max_span_minutes": round(max(
            ((g[0]["mtime_ns"] - g[-1]["mtime_ns"]) / 6e10 for g in groups),
            default=0), 2),
    }


def measure(repo, git):
    def run(*args):
        result = git.run(repo, *args, read_only=True)
        if not result.ok:
            raise RuntimeError(result.message)
        return result.stdout

    index = Path(os.fsdecode(run("rev-parse", "--git-path", "index").strip()))
    if not index.is_absolute():
        index = repo / index

    def index_hash():
        return hashlib.sha256(index.read_bytes()).hexdigest() if index.exists() else None

    before = index_hash()
    started = time.perf_counter()
    raw = run(*STATUS_ARGS)
    status_ms = 1000 * (time.perf_counter() - started)
    changes = parse_status(raw).changes
    paths = {}
    for change in changes:
        paths.setdefault(change.path, []).append(change.group.value)
    started = time.perf_counter()
    rows = []
    for path, groups in paths.items():
        try:
            modified = (repo / path).lstat().st_mtime_ns
            error = None
        except OSError as exc:
            modified, error = None, type(exc).__name__
        rows.append({
            "path": path, "groups": groups, "mtime_ns": modified,
            "modified": datetime.fromtimestamp(modified / 1e9).astimezone().isoformat()
            if modified is not None else None, "error": error,
        })
    stat_ms = 1000 * (time.perf_counter() - started)
    started = time.perf_counter()
    sweeps = {str(gap): stats(rows, gap) for gap in THRESHOLDS}
    calc_ms = 1000 * (time.perf_counter() - started)
    return {
        "repo": repo.name, "root": str(repo), "files": len(rows),
        "rows": len(changes), "missing_time": sum(r["mtime_ns"] is None for r in rows),
        "status_ms": round(status_ms, 2), "stat_ms": round(stat_ms, 2),
        "six_thresholds_ms": round(calc_ms, 2), "index_unchanged": before == index_hash(),
        "index_sha256": before, "status_sha256": hashlib.sha256(raw).hexdigest(),
        "thresholds": sweeps,
        "per_status": {group: {str(gap): stats(
            [r for r in rows if group in r["groups"]], gap) for gap in THRESHOLDS}
            for group in ("Staged", "Changes", "Unversioned", "Conflicts")},
        "bounded_5m_gap_15m_span": stats(rows, 300, 900), "files_data": rows,
        "groups_5m": [{"start": g[-1]["modified"], "end": g[0]["modified"],
                       "files": [r["path"] for r in g]} for g in clusters(rows, 300)],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("repos", nargs="+", type=Path)
    args = parser.parse_args()
    report = {"measured_at": datetime.now().astimezone().isoformat(),
              "threshold_seconds": THRESHOLDS,
              "repos": [measure(repo.resolve(), GitCli()) for repo in args.repos]}
    # Exclusive creation avoids overwriting any existing file, including repo files.
    with args.output.open("x") as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(json.dumps({"output": str(args.output), "repos": [
        {k: r[k] for k in ("repo", "files", "missing_time", "index_unchanged")}
        for r in report["repos"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
