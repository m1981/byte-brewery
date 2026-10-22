"""Memory, refresh time and idleness of the real app, measured in its own process (DES-VCS-034, DES-VCS-047).

The window shows on screen for a few seconds. tests/measure_footprint.py measures; these tests judge,
and every failure prints the whole measurement.
"""

from __future__ import annotations

import json
import shutil

import measure_footprint
import pytest


@pytest.fixture(scope="module")
def measured() -> dict:
    if shutil.which("footprint") is None:
        pytest.skip("footprint is macOS only")
    return measure_footprint.measure()


def report(measurement: dict) -> str:
    return json.dumps(measurement, indent=2, ensure_ascii=False)


def test_at_vcs_016_vcs_lite_stays_within_60_mb_with_an_open_compare(measured):
    assert len(measured["footprint_mib"]) == 5
    assert measured["footprint_mib_max"] <= 60, report(measured)


def test_req_vcs_102_refreshing_300_changes_takes_under_a_second(measured):
    assert len(measured["refresh_s"]) == 5 and measured["changes"] == 300
    assert measured["refresh_s_median"] < 1.0, report(measured)


def test_req_vcs_101_no_git_calls_while_idle_with_an_open_compare(measured):
    assert measured["git_calls_before_ready"] > 0  # the log works, so zero below means idle
    assert measured["git_calls_while_idle"] == 0, report(measured)
