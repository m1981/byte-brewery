"""Footprint and refresh time of vcs-lite under the conditions of REQ-VCS-100 (DES-VCS-034, DES-VCS-047).

Usage: python tests/measure_footprint.py [--bcomp] [--idle SECONDS]

Builds 3 repositories in a temporary folder (one with 300 changed files, among them one of 2000 lines),
starts vcs-lite in its own process group, refreshes the big repository 1 + 5 times, opens the long file
in the diff tool and announces "ready". From then on the app is idle: `footprint -j` samples only the
vcs-lite process once a second, and the git call log must stay silent. Prints one JSON object; it only
measures, tests/test_footprint.py judges.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import select
import signal
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vcs_lite.core.gitcli import GIT_LOG_ENV, append_log  # noqa: E402

BIG, OTHERS = "duzy", ("drugi", "trzeci")
CHANGES = 300
LONG_FILE, LONG_LINES = "dlugi.py", 2000
REFRESHES = 5
READY_TIMEOUT, TOOL_TIMEOUT, SETTLE_TIMEOUT, TERM_GRACE = 90.0, 60.0, 30.0, 3.0
BCOMP = ["/Applications/Beyond Compare.app/Contents/MacOS/bcomp", "{left}", "{right}",
         "-title1={left_title}", "-title2={right_title}"]
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "Pomiar", "GIT_AUTHOR_EMAIL": "pomiar@example.invalid",
           "GIT_COMMITTER_NAME": "Pomiar", "GIT_COMMITTER_EMAIL": "pomiar@example.invalid"}


# ---------- the environment of REQ-VCS-100 ----------

def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], env={**os.environ, **GIT_ENV},
                          capture_output=True, text=True, check=True).stdout


def build_environment(base: Path, *, bcomp: bool) -> Path:
    rootdir = base / "root"
    big = rootdir / BIG
    big.mkdir(parents=True)
    git(big, "init", "-q", "-b", "main")
    small = [big / f"plik_{i:03}.txt" for i in range(CHANGES - 1)]
    (big / LONG_FILE).write_text("".join(f"line_{i} = {i}\n" for i in range(LONG_LINES)))
    for i, path in enumerate(small):
        path.write_text(f"{i}\n")
    git(big, "add", "-A"); git(big, "commit", "-q", "-m", "base")
    (big / LONG_FILE).write_text("".join(f"line_{i} = {i * 2}\n" for i in range(LONG_LINES)))
    for i, path in enumerate(small):
        path.write_text(f"{i} zmiana\n")
    for name in OTHERS:
        repo = rootdir / name
        repo.mkdir()
        git(repo, "init", "-q", "-b", "main")
        (repo / "a.txt").write_text("a\n")
        git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "base")
        (repo / "a.txt").write_text("a2\n")
    tool = BCOMP if bcomp else [sys.executable, str(HERE / "waiting_difftool.py"), "{left}", "{right}"]
    settings = base / "settings.json"
    settings.write_text(json.dumps({"rootdir": str(rootdir), "repos": [BIG, *OTHERS], "diff_tool": tool}))
    return settings


# ---------- the measured process ----------

def run_child(settings: Path) -> None:
    from vcs_lite.core.status import Group
    from vcs_lite.ui.main import build

    root, model, pump = build(settings)
    root.update()
    model.refresh_all()
    settle(root, pump)
    model.select(BIG)
    settle(root, pump)
    times = [timed_refresh(root, model, pump) for _ in range(REFRESHES + 1)][1:]  # the first one is cold
    changes = sum(len(model.files(group)) for group in Group)
    model.activate(next(c for c in model.files(Group.CHANGES) if c.path == LONG_FILE))
    wait_for_diff_tool(root)
    append_log(os.environ[GIT_LOG_ENV], {"t": time.monotonic(), "pid": os.getpid(), "event": "ready"})
    print(json.dumps({"ready": True, "pid": os.getpid(), "refresh_s": times, "changes": changes,
                      "tk": str(root.tk.call("info", "patchlevel"))}), flush=True)
    root.mainloop()


def settle(root, pump) -> None:
    """Run the Tk loop until no operation is pending."""
    deadline = time.monotonic() + SETTLE_TIMEOUT
    root.update()
    while pump.polling:
        if time.monotonic() > deadline:
            raise TimeoutError(f"operacje nie skończyły się w {SETTLE_TIMEOUT:g} s")
        root.update()
        time.sleep(0.002)
    root.update_idletasks()


def timed_refresh(root, model, pump) -> float:
    start = time.perf_counter()
    model.refresh(BIG)
    settle(root, pump)
    return time.perf_counter() - start


def wait_for_diff_tool(root) -> None:
    """The compare is open when the diff tool runs as our child and no git call (reading the sides) is left."""
    deadline = time.monotonic() + TOOL_TIMEOUT
    while True:
        out = subprocess.run(["pgrep", "-lP", str(os.getpid())], capture_output=True, text=True).stdout
        names = [line.split(maxsplit=1)[1] for line in out.splitlines() if " " in line]
        if names and "git" not in names:
            return
        if time.monotonic() > deadline:
            raise TimeoutError(f"narzędzie diffu nie wystartowało w {TOOL_TIMEOUT:g} s")
        root.update()
        time.sleep(0.05)


# ---------- the measuring process ----------

def measure(*, bcomp: bool = False, idle: int = 5) -> dict:
    with tempfile.TemporaryDirectory(prefix="vcs-lite-pomiar-") as tmp:
        base = Path(tmp)
        settings = build_environment(base, bcomp=bcomp)
        log = base / "git.log"
        env = {**os.environ, **GIT_ENV, GIT_LOG_ENV: str(log), "PYTHONPATH": str(SRC)}
        proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--child", str(settings)],
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                start_new_session=True)
        try:
            ready = read_ready(proc)
            start = time.monotonic()
            samples = []
            for second in range(1, idle + 1):
                time.sleep(max(0.0, start + second - time.monotonic()))
                samples.append(footprint_mib(proc.pid, base / f"footprint-{second}.json"))
            idle_end = time.monotonic()
        finally:
            stop(proc)
        records = [json.loads(line) for line in log.read_text().splitlines()]
    ready_t = next(r["t"] for r in records if r.get("event") == "ready")
    calls = [r for r in records if "cmd" in r]
    return {
        "date": datetime.now().astimezone().isoformat(timespec="seconds"),
        "python": platform.python_version(), "tk": ready["tk"], "macos": platform.mac_ver()[0],
        "git": git(HERE, "--version").strip(), "commit": source_version(),
        "diff_tool": "bcomp" if bcomp else "atrapa (tests/waiting_difftool.py)",
        "changes": ready["changes"], "idle_s": idle,
        "footprint_mib": [round(s, 1) for s in samples], "footprint_mib_max": round(max(samples), 1),
        "refresh_s": [round(t, 3) for t in ready["refresh_s"]],
        "refresh_s_median": round(statistics.median(ready["refresh_s"]), 3),
        "git_calls_before_ready": sum(1 for r in calls if r["t"] <= ready_t),
        "git_calls_while_idle": sum(1 for r in calls if ready_t < r["t"] <= idle_end),
    }


def read_ready(proc: subprocess.Popen) -> dict:
    deadline = time.monotonic() + READY_TIMEOUT
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"vcs-lite zakończył się kodem {proc.returncode}:\n{proc.stderr.read()}")
        readable, _, _ = select.select([proc.stdout], [], [], 0.2)
        if readable:
            line = proc.stdout.readline()
            if line.strip():
                return json.loads(line)
    raise TimeoutError(f"vcs-lite nie zgłosił gotowości w {READY_TIMEOUT:g} s")


def footprint_mib(pid: int, out: Path) -> float:
    subprocess.run(["footprint", "-j", str(out), str(pid)], capture_output=True, timeout=10, check=True)
    process = next(p for p in json.loads(out.read_text())["processes"] if p["pid"] == pid)
    return process["footprint"] / 2**20  # the "MB" of footprint and Activity Monitor


def stop(proc: subprocess.Popen) -> None:
    """End vcs-lite and its diff tool: the whole process group, politely and then for sure."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            break
        try:
            proc.wait(timeout=TERM_GRACE)
            break
        except subprocess.TimeoutExpired:
            continue
    for stream in (proc.stdout, proc.stderr):
        stream.close()


def source_version() -> str:
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}  # describe --dirty must not rewrite the user's index
    return subprocess.run(["git", "-C", str(HERE), "describe", "--always", "--dirty"],
                          env=env, capture_output=True, text=True).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bcomp", action="store_true", help="prawdziwy Beyond Compare zamiast atrapy")
    parser.add_argument("--idle", type=int, default=5, help="sekundy bezczynności z próbkami co 1 s")
    parser.add_argument("--child", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        run_child(args.child)
    else:
        print(json.dumps(measure(bcomp=args.bcomp, idle=args.idle), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
