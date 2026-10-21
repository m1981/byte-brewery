"""Worker: operations off the UI thread, one per key, results delivered by drain() (DES-VCS-016, DES-VCS-017)."""

from __future__ import annotations

import threading
import time

from vcs_lite.app.worker import Outcome, Worker


def wait_until(predicate, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < deadline, "timed out"
        time.sleep(0.01)


def test_des_vcs_016_second_operation_on_a_busy_repo_is_rejected():
    worker, release = Worker(), threading.Event()
    assert worker.submit("alpha", release.wait, lambda o: None)
    assert worker.busy("alpha")
    assert not worker.submit("alpha", lambda: None, lambda o: None)
    release.set()


def test_des_vcs_016_another_repo_can_run_meanwhile():
    worker, release = Worker(), threading.Event()
    worker.submit("alpha", release.wait, lambda o: None)
    assert worker.submit("beta", lambda: None, lambda o: None)
    release.set()


def test_des_vcs_017_results_are_delivered_only_by_drain_on_the_calling_thread():
    worker, delivered = Worker(), []
    worker.submit("alpha", lambda: 42, lambda o: delivered.append((o, threading.current_thread())))
    wait_until(lambda: worker.ready())
    assert delivered == []
    assert worker.drain() == 1
    assert delivered == [(Outcome(value=42), threading.current_thread())]


def test_des_vcs_017_the_key_stays_busy_until_drained_and_then_frees():
    worker = Worker()
    worker.submit("alpha", lambda: None, lambda o: None)
    wait_until(lambda: worker.ready())
    assert worker.busy("alpha")
    worker.drain()
    assert not worker.busy("alpha")


def test_des_vcs_017_nothing_is_pending_while_idle_so_the_ui_stops_polling():
    worker = Worker()
    assert not worker.pending
    worker.submit("alpha", lambda: None, lambda o: None)
    assert worker.pending
    wait_until(lambda: worker.ready())
    worker.drain()
    assert not worker.pending


def test_des_vcs_016_a_failing_job_delivers_its_error():
    worker, delivered = Worker(), []

    def boom():
        raise RuntimeError("nie wyszło")

    worker.submit("alpha", boom, delivered.append)
    wait_until(lambda: worker.ready())
    worker.drain()
    assert isinstance(delivered[0].error, RuntimeError) and delivered[0].value is None


def test_des_vcs_016_on_done_may_schedule_a_follow_up_on_the_same_key():
    worker, order = Worker(), []
    worker.submit("alpha", lambda: "commit", lambda o: (order.append(o.value),
                                                        worker.submit("alpha", lambda: "refresh", lambda o2: order.append(o2.value))))
    wait_until(lambda: worker.ready())
    worker.drain()
    wait_until(lambda: worker.ready())
    worker.drain()
    assert order == ["commit", "refresh"]
