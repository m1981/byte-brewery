"""Footprint and refresh time of vcs-lite under the conditions of REQ-VCS-100 (DES-VCS-034, DES-VCS-047).

Usage: python tests/measure_footprint.py [--idle SECONDS] [--changes 3000 --exercise]

Builds 3 repositories in a temporary folder (one with 300 changed files, among them one of 2000 lines,
and a history of HISTORY commits with a branch merged every MERGE_EVERY, shown in the history panel),
starts vcs-lite in its own process group, refreshes the big repository 1 + 5 times, opens the long file
in the diff tool plugin (a stand-in that waits, so the compare stays open; a browser page would end at once
and would open a tab) and announces "ready". From then on the app is idle: `footprint -j` samples only the
vcs-lite process once a second, and the git call log must stay silent. The window stays topmost throughout.
With --exercise, also measure mouse/keyboard, scroll, resize and view switching with a Tk heartbeat.
Prints one JSON object; it only
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
HISTORY, MERGE_EVERY = 4000, 40   # like the user's largest repository, pi-mono (OBS-VCS-016)
READY_TIMEOUT, TOOL_TIMEOUT, SETTLE_TIMEOUT, TERM_GRACE = 90.0, 60.0, 30.0, 3.0
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "Pomiar", "GIT_AUTHOR_EMAIL": "pomiar@example.invalid",
           "GIT_COMMITTER_NAME": "Pomiar", "GIT_COMMITTER_EMAIL": "pomiar@example.invalid"}


# ---------- the environment of REQ-VCS-100 ----------

def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], env={**os.environ, **GIT_ENV},
                          capture_output=True, text=True, check=True).stdout


def history_stream(commits: int, merge_every: int) -> bytes:
    """`git fast-import` input: a main line with a two-commit side branch merged every `merge_every`."""
    out, mark, time_ = [], 0, 1_700_000_000

    def blob_commit(ref: str, message: str, parents: list[int], path: str) -> int:
        nonlocal mark, time_
        mark, time_ = mark + 1, time_ + 60
        data, content = message.encode(), f"{message}\n".encode()
        out.append(f"commit {ref}\nmark :{mark}\nauthor Pomiar <p@x> {time_} +0000\n"
                   f"committer Pomiar <p@x> {time_} +0000\ndata {len(data)}\n".encode() + data + b"\n")
        if parents:
            out.append(f"from :{parents[0]}\n".encode())
        out.extend(f"merge :{p}\n".encode() for p in parents[1:])
        out.append(f"M 644 inline {path}\ndata {len(content)}\n".encode() + content + b"\n")
        return mark

    head = blob_commit("refs/heads/main", "commit 0", [], "historia.txt")
    made = 1
    while made < commits:
        if made % merge_every == 0 and made + 3 <= commits:
            side = blob_commit("refs/heads/side", f"side {made}", [head], "side.txt")
            side = blob_commit("refs/heads/side", f"side {made} b", [side], "side.txt")
            main = blob_commit("refs/heads/main", f"main {made}", [head], "historia.txt")
            head = blob_commit("refs/heads/main", f"merge {made}", [main, side], "historia.txt")
            made += 4
        else:
            head = blob_commit("refs/heads/main", f"commit {made}", [head], "historia.txt")
            made += 1
    return b"".join(out)


def build_environment(base: Path, changes: int = CHANGES) -> Path:
    rootdir = base / "root"
    big = rootdir / BIG
    big.mkdir(parents=True)
    git(big, "init", "-q", "-b", "main")
    subprocess.run(["git", "-C", str(big), "fast-import", "--quiet"], input=history_stream(HISTORY - 1, MERGE_EVERY),
                   env={**os.environ, **GIT_ENV}, check=True, capture_output=True)
    git(big, "reset", "-q", "--hard", "main")
    small = [big / f"plik_{i:04}.txt" for i in range(changes - 1)]
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
    tool = [sys.executable, str(HERE / "waiting_difftool.py"), "{left}", "{right}"]
    settings = base / "settings.json"
    settings.write_text(json.dumps({"rootdir": str(rootdir), "repos": [BIG, *OTHERS], "external_diff_tool": tool}))
    return settings


# ---------- the measured process ----------

class Heartbeat:
    """Largest gap in the real Tk event loop, including synchronous drawing work."""
    def __init__(self, root):
        self.root, self.last, self.maximum = root, time.perf_counter(), 0.0
        self.count = 0
        self.token = root.after(20, self.tick)

    def tick(self):
        now = time.perf_counter()
        self.maximum = max(self.maximum, now - self.last)
        self.last = now
        self.count += 1
        self.token = self.root.after(20, self.tick)

    def stop(self):
        self.maximum = max(self.maximum, time.perf_counter() - self.last)
        self.root.after_cancel(self.token)


def isolate_input(root) -> None:
    """Keep desktop pointer/focus activity from changing the benchmark's scripted workload.

    Production handlers are called by exercise_window; Expose, Configure, timers, painting and
    the worker still run normally. This also prevents an accidental native Leave from clearing
    the hover under test, or a wheel event from loading unrelated history pages.
    """
    tag = "VcsBenchmarkInput"
    for event in ("<Motion>", "<Enter>", "<Leave>", "<MouseWheel>", "<ButtonPress>", "<ButtonRelease>",
                  "<KeyPress>", "<KeyRelease>"):
        root.bind_class(tag, event, lambda _e: "break")

    def visit(widget):
        widget.bindtags((tag, *widget.bindtags()))
        for child in widget.winfo_children():
            visit(child)
    visit(root)


def exercise_window(root, window, model, pump) -> dict:
    """Use the production handlers, then flush Tk/native drawing before stopping each timer."""
    fl, samples, completed, objects = window.file_list, {}, {}, []
    details, detail_objects = window.history.details, []

    def act(name, action):
        start = time.perf_counter()
        action()
        root.update()  # dispatch and actual drawing; background Git need not be complete for the UI to respond
        samples[name] = round(time.perf_counter() - start, 4)
        settle(root, pump)
        completed[name] = round(time.perf_counter() - start, 4)
        objects.append(len(fl.canvas.find_all()))
        detail_objects.append(len(details.canvas.find_all()))

    for view in ("changes", "folders", "project"):
        act(f"{view}:view", lambda v=view: window.set_list_view(v))
        rows = fl.rows()
        for label, index in (("first", 0), ("middle", len(rows) // 2), ("last", len(rows) - 1)):
            row = rows[index]
            act(f"{view}:{label}:select", lambda r=row: fl.select_key(r.key))
            assert fl.selected_key == row.key
            assert fl.canvas.canvasy(0) <= row.top + row.height
            assert row.top < fl.canvas.canvasy(fl.canvas.winfo_height())
            # Invoke the bound handlers directly: native synthetic keys depend on OS focus,
            # even in a mapped topmost window. Keep real Tk/native drawing in act().
            y = round(row.top + row.height / 2 - fl.canvas.canvasy(0))
            act(f"{view}:{label}:hover", lambda y=y: fl.hover(y))
            assert fl.hovered_key == row.key, (view, label, fl.hovered_key, row.key)
            act(f"{view}:{label}:up", fl.press_up)
            assert fl.selected_key == rows[max(0, index - 1)].key
            act(f"{view}:{label}:down", fl.press_down)
            assert fl.selected_key == rows[min(max(0, index - 1) + 1, len(rows) - 1)].key
        act(f"{view}:wheel", lambda: fl.scroll(120))
        act(f"{view}:home", lambda: fl.canvas.yview_moveto(0))
    act("resize:narrow", lambda: root.geometry("850x700"))
    act("resize:wide", lambda: root.geometry("1100x820"))
    act("changes:return", lambda: window.set_list_view("changes"))
    for i in range(12):
        y = 150 + (i % 6) * 24
        act(f"hover-burst:{i}", lambda y=y: fl.hover(y))
    for i, fraction in enumerate((0, 0.5, 1, 0)):
        act(f"commit-files:{i}:scroll", lambda f=fraction: details.canvas.yview_moveto(f))
        act(f"commit-files:{i}:hover", lambda: details._set_hover(details.file_index_at(120)))
    return {"interaction_s": samples, "operation_s": completed, "canvas_items_max": max(objects),
            "history_detail_items_max": max(detail_objects)}


def run_child(settings: Path, *, exercise: bool = False) -> None:
    from vcs_lite.core.status import Group
    from vcs_lite.ui.main import build
    from vcs_lite.ui.main_window import MainWindow

    root, model, pump = build(settings)
    isolate_input(root)
    # Keep it above other windows for the ENTIRE measurement, including idle samples.
    root.attributes("-topmost", True)
    root.lift()
    root.update()
    model.refresh_all()
    settle(root, pump)
    model.select(BIG)
    settle(root, pump)
    window = next(w for w in root.winfo_children() if isinstance(w, MainWindow))
    heartbeat = Heartbeat(root)
    interactions = exercise_window(root, window, model, pump) if exercise else {}
    times = [timed_refresh(root, model, pump) for _ in range(REFRESHES + 1)][1:]  # the first one is cold
    heartbeat.stop()
    changes = sum(len(model.files(group)) for group in Group)
    history = window.history.session
    model.activate(next(c for c in model.files(Group.CHANGES) if c.path == LONG_FILE), external=True)
    wait_for_diff_tool(root)
    append_log(os.environ[GIT_LOG_ENV], {"t": time.monotonic(), "pid": os.getpid(), "event": "ready"})
    print(json.dumps({"ready": True, "pid": os.getpid(), "refresh_s": times, "changes": changes,
                      "history_loaded": len(history.commits), "history_total": history.count,
                      "topmost": bool(root.attributes("-topmost")), "viewable": bool(root.winfo_viewable()),
                      "heartbeat_max_s": round(heartbeat.maximum, 4), "heartbeat_count": heartbeat.count,
                      **interactions,
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

def measure(*, idle: int = 5, changes: int = CHANGES, exercise: bool = False) -> dict:
    with tempfile.TemporaryDirectory(prefix="vcs-lite-pomiar-") as tmp:
        base = Path(tmp)
        settings = build_environment(base, changes)
        log = base / "git.log"
        env = {**os.environ, **GIT_ENV, GIT_LOG_ENV: str(log), "PYTHONPATH": str(SRC)}
        command = [sys.executable, str(Path(__file__).resolve()), "--child", str(settings)]
        if exercise:
            command.append("--exercise")
        proc = subprocess.Popen(command,
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
        "diff_tool": "wtyczka external_diff_tool z atrapą (tests/waiting_difftool.py)",
        "changes": ready["changes"], "idle_s": idle,
        "history_loaded": ready["history_loaded"], "history_total": ready["history_total"],
        "topmost": ready["topmost"], "viewable": ready["viewable"],
        "heartbeat_max_s": ready["heartbeat_max_s"], "heartbeat_count": ready["heartbeat_count"],
        "interaction_s": ready.get("interaction_s", {}), "canvas_items_max": ready.get("canvas_items_max", 0),
        "operation_s": ready.get("operation_s", {}),
        "history_detail_items_max": ready.get("history_detail_items_max", 0),
        "footprint_mib": [round(s, 1) for s in samples], "footprint_mib_max": round(max(samples), 1),
        "refresh_s": [round(t, 3) for t in ready["refresh_s"]],
        "refresh_s_median": round(statistics.median(ready["refresh_s"]), 3),
        "git_calls_before_ready": sum(1 for r in calls if r["t"] <= ready_t),
        "git_calls_while_idle": sum(1 for r in calls if ready_t < r["t"] <= idle_end),
        "git_calls_while_idle_detail": [f'{r["cmd"]} +{r["t"] - ready_t:.2f} s' for r in calls
                                        if ready_t < r["t"] <= idle_end],  # e.g. a refresh after a focus change
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
    parser.add_argument("--idle", type=int, default=5, help="sekundy bezczynności z próbkami co 1 s")
    parser.add_argument("--child", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--changes", type=int, default=CHANGES, help="liczba zmienionych plików (np. 3000)")
    parser.add_argument("--exercise", action="store_true", help="zmierz przewijanie, klawiaturę, hover i zmianę widoku")
    args = parser.parse_args()
    if args.child:
        run_child(args.child, exercise=args.exercise)
    else:
        print(json.dumps(measure(idle=args.idle, changes=args.changes, exercise=args.exercise), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
